from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from evals.harness.gate import BASELINES, answer_checks, main, retrieval_checks

REPORTS = Path("evals/reports")
BASE = yaml.safe_load(BASELINES.read_text(encoding="utf-8"))


def load(name: str) -> dict[str, Any]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def test_committed_baselines_pass_their_own_reports() -> None:
    (r,) = retrieval_checks(load("2026-10-15-c756c89-retrieval.json"), BASE["retrieval"])
    assert r.ok
    assert all(
        c.ok for c in answer_checks(load("2026-10-15-7d081e6-smoke-drafts.json"), BASE["answers"])
    )


def test_retrieval_drop_beyond_tolerance_fails() -> None:
    report = load("2026-10-15-c756c89-retrieval.json")
    report["results"][0]["summary"]["recall@8"]["mean"] = 0.96  # 98.5 - 2.5
    assert not retrieval_checks(report, BASE["retrieval"])[0].ok
    report["results"][0]["summary"]["recall@8"]["mean"] = 0.966  # within 2 pts
    assert retrieval_checks(report, BASE["retrieval"])[0].ok


@pytest.mark.parametrize(
    ("patch", "failing"),
    [
        ({"quote_fidelity": {"verbatim": 71, "quotes": 72, "rate": 71 / 72}}, "quote fidelity"),
        ({"hallucinated_citations": {"count": 1, "citations": 72}}, "hallucinated citations"),
        ({"errors": 2}, "agent errors (20 cases)"),
        ({"quote_fidelity": {"verbatim": 0, "quotes": 0, "rate": None}}, "quote fidelity"),
    ],
)
def test_answer_gates_fail(patch: dict[str, Any], failing: str) -> None:
    report = copy.deepcopy(load("2026-10-15-7d081e6-smoke-drafts.json"))
    for k, v in patch.items():
        report["summary"][k] = report["summary"][k] | v if isinstance(v, dict) else v
    failed = [c.name for c in answer_checks(report, BASE["answers"]) if not c.ok]
    assert failed == [failing]


def test_main_exit_code_and_step_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    ok = main(["--answers", str(REPORTS / "2026-10-15-7d081e6-smoke-drafts.json")])
    assert ok == 0
    text = summary.read_text(encoding="utf-8")
    assert "| quote fidelity | 100.0% (72/72)" in text
    assert "not a headline number" in text
    bad = load("2026-10-15-7d081e6-smoke-drafts.json")
    bad["summary"]["errors"] = 5
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert main(["--answers", str(path)]) == 1


def test_a_run_where_every_case_errored_fails_with_a_table(tmp_path: Path) -> None:
    bad = load("2026-10-15-7d081e6-smoke-drafts.json")
    s = bad["summary"]
    s["errors"] = s["cases"]
    s["quote_fidelity"] = {"verbatim": 0, "quotes": 0, "rate": None}
    s["latency_s"]["p50"] = None
    s["cost_per_answer"]["chf"] = None
    s["run_cost_chf"] = {"agent": 0.0}
    path = tmp_path / "errored.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert main(["--answers", str(path)]) == 1
