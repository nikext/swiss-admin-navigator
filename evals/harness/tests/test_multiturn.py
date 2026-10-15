from __future__ import annotations

import json

import pytest

from evals.harness.multiturn import METRIC, agent_cost_chf, agent_reply, summarize_case


def test_agent_reply_extracts_user_facing_parts() -> None:
    raw = json.dumps(
        {
            "answer_markdown": "It depends on your permit.",
            "clarifying_question": "Which permit do you have?",
            "citations": [{"abbr": "AIG", "article": "Art. 43"}],
        }
    )
    assert agent_reply(raw) == (
        "It depends on your permit.\n[asks] Which permit do you have?\n[cites] AIG Art. 43"
    )
    assert agent_reply("not json") == "not json"


TOKENS = {"prompt_tokens": 100, "cached_tokens": 40}


def content(text: str) -> dict:
    return {"parts": [{"text": "thinking", "thought": True}, {"text": text}]}


def test_summarize_case_reads_rubrics_transcript_and_tokens() -> None:
    case = {
        "eval_id": "mt-01",
        "final_eval_status": 1,
        "overall_eval_metric_results": [{"metric_name": METRIC, "score": 0.5}],
        "eval_metric_result_per_invocation": [
            {
                "actual_invocation": {
                    "user_content": content("Can my wife come?"),
                    "final_response": content(json.dumps({"answer_markdown": "Which permit?"})),
                },
                "eval_metric_results": [
                    {
                        "metric_name": "token_usage_v1",
                        "details": {"token_usage_details": TOKENS},
                    }
                ],
            },
            {
                "actual_invocation": {
                    "user_content": content("C permit."),
                    "final_response": content("plain text"),
                },
                "eval_metric_results": [
                    {
                        "metric_name": METRIC,
                        "details": {
                            "rubric_scores": [
                                {"rubric_id": "mt-01-r1", "score": 1.0, "rationale": "asked"},
                                {"rubric_id": "mt-01-r2", "score": 0.0, "rationale": "no cite"},
                            ]
                        },
                    },
                    {
                        "metric_name": "token_usage_v1",
                        "details": {"token_usage_details": {"prompt_tokens": 50}},
                    },
                ],
            },
        ],
    }
    row = summarize_case(case, {"mt-01-r1": "asks first", "mt-01-r2": "cites"})
    assert row["score"] == 0.5
    assert row["status"] == "passed"
    assert row["turns"] == 2
    assert row["transcript"][0] == {"user": "Can my wife come?", "agent": "Which permit?"}
    assert [v["rubric"] for v in row["rubrics"]] == ["asks first", "cites"]
    assert row["tokens"] == {"prompt_tokens": 150, "cached_tokens": 40}


def test_agent_cost() -> None:
    pricing = {
        "usd_to_chf": 1.0,
        "models": {"m": {"input": 1.0, "cached_input": 0.1, "output": 10.0}},
    }
    tokens = {"prompt_tokens": 1_000_000, "cached_tokens": 500_000, "candidates_tokens": 100_000}
    assert agent_cost_chf(tokens, "m", pricing) == pytest.approx(0.5 + 0.05 + 1.0)
    assert agent_cost_chf(tokens, "unknown", pricing) is None
