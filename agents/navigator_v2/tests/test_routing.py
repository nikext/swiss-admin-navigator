"""navigator_v2's routing logic and construction (behaviour is tested through evals)."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from google.adk.workflow import Workflow

from agents.navigator.agent import PROMPT
from agents.navigator_v2.agent import (
    ROUTE_KEY,
    build_router,
    build_workflow,
    scoped_search,
    specialist_prompt,
)
from agents.navigator_v2.routing import (
    DOMAIN_ACTS,
    GENERALIST,
    SPECIALISTS,
    Route,
    dispatch,
    route_scope,
    scope_search_args,
    search_scope,
)

ACTS_YAML = Path(__file__).parents[3] / "corpus" / "acts.yaml"


def test_domain_acts_mirror_the_corpus() -> None:
    acts = yaml.safe_load(ACTS_YAML.read_text(encoding="utf-8"))["acts"]
    expected: dict[str, set[str]] = {}
    for act in acts:
        domains = act["domain"] if isinstance(act["domain"], list) else [act["domain"]]
        for d in domains:
            expected.setdefault(d, set()).add(act["sr"])
    assert {d: set(srs) for d, srs in DOMAIN_ACTS.items()} == expected
    assert set(SPECIALISTS) | {GENERALIST} == set(expected)


@pytest.mark.parametrize(
    ("route", "domain"),
    [
        ({"language": "de", "domains": ["work"]}, "work"),
        ({"language": "en", "domains": ["tax", "residence"]}, "tax"),  # primary domain
        ({"language": "fr", "domains": ["general", "housing"]}, "general"),
        ({"language": "it", "domains": []}, "general"),
        ({"language": "xx", "domains": ["work"]}, "general"),  # invalid route
        ({"raw": "not json"}, "general"),
        (None, "general"),
        (Route(language="en", domains=["mobility"]), "mobility"),
    ],
)
def test_dispatch(route: Any, domain: str) -> None:
    assert dispatch(route) == domain


def test_search_scope() -> None:
    assert search_scope(["tax"]) == ["642.11", "642.14", "642.118.2", "101", "210", "235.1"]
    work_housing = search_scope(["work", "housing"])
    assert work_housing.count("220") == 1  # OR serves both
    assert "221.213.11" in work_housing
    assert search_scope(["general", "tax"]) == []  # the generalist searches everything
    assert search_scope([]) == []
    assert route_scope(None, "mobility") == search_scope(["mobility"])
    assert route_scope({"language": "en", "domains": ["tax", "residence"]}, "tax") == (
        search_scope(["tax", "residence"])
    )


def test_scope_search_args() -> None:
    args: dict[str, Any] = {"query": "x"}
    scope_search_args(args, ["642.11"])
    assert args["sr"] == ["642.11"]
    args = {"query": "x", "sr": ["220"]}  # the model's choice wins
    scope_search_args(args, ["642.11"])
    assert args["sr"] == ["220"]
    args = {"query": "x", "sr": []}  # all acts
    scope_search_args(args, ["642.11"])
    assert "sr" not in args
    args = {"query": "x"}
    scope_search_args(args, [])  # generalist: no filter
    assert "sr" not in args


class Tool:
    def __init__(self, name: str) -> None:
        self.name = name


class Ctx:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state


def test_scoped_search_reads_the_route_from_state() -> None:
    before = scoped_search("tax")
    args: dict[str, Any] = {"query": "x"}
    route = {"language": "en", "domains": ["tax", "residence"]}
    before(Tool("search_law"), args, Ctx({ROUTE_KEY: route}))  # type: ignore[arg-type]
    assert args["sr"] == search_scope(["tax", "residence"])
    other: dict[str, Any] = {"sr": "220", "article": "1"}
    before(Tool("get_article"), other, Ctx({}))  # type: ignore[arg-type]
    assert other == {"sr": "220", "article": "1"}


def test_specialist_prompt_extends_v1() -> None:
    p = specialist_prompt("residence")
    assert p.startswith(PROMPT.rstrip())
    assert "## Your domain" in p
    assert "residence and citizenship" in p
    assert "142.20" in p


def test_workflow_construction() -> None:
    wf = build_workflow("http://127.0.0.1:1/mcp", claim_check=True)
    assert isinstance(wf, Workflow)
    router = build_router()
    assert router.mode == "chat"
    assert router.output_key == ROUTE_KEY
    assert router.output_schema is Route
    assert not router.tools
