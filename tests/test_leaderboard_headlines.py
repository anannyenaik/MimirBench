"""Evidence-gated headline candidate extraction."""

from __future__ import annotations

from mimirbench.evals.leaderboard import propose_headline_candidates


def test_no_metrics_produce_no_headline_candidates() -> None:
    assert propose_headline_candidates(
        {
            "preliminary": True,
            "tasks_per_agent": 0,
            "paired_metrics": {},
            "leaderboard": [],
        }
    ) == []


def test_tool_headline_requires_supporting_metrics() -> None:
    candidates = propose_headline_candidates(
        {
            "preliminary": True,
            "tasks_per_agent": 10,
            "paired_metrics": {
                "configured_model": {
                    "tool_vs_direct": {
                        "n_pairs": 10,
                        "mean_score_difference": 0.12,
                        "mean_risk_violation_difference": 0.0,
                    }
                }
            },
            "leaderboard": [],
        }
    )

    assert len(candidates) == 1
    assert "tool use improved mean score" in candidates[0]["text"]
    assert candidates[0]["preliminary"] is True
    assert candidates[0]["evidence"]["n_pairs"] == 10


def test_missing_supporting_metric_suppresses_candidate() -> None:
    candidates = propose_headline_candidates(
        {
            "preliminary": True,
            "tasks_per_agent": 10,
            "paired_metrics": {
                "configured_model": {
                    "tool_vs_direct": {
                        "n_pairs": 10,
                        "mean_score_difference": 0.12,
                    }
                }
            },
            "leaderboard": [],
        }
    )

    assert candidates == []
