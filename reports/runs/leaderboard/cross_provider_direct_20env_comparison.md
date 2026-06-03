# Preliminary cross-provider direct comparison

Generated from saved artefacts on 2026-06-03 local time. This is a synthetic,
direct-agent-only comparison with 20 tasks per environment across six
environments. It compares one Anthropic model against the completed OpenAI
`gpt-5.4` direct row only. It is not statistically conclusive, not a trading
result, and not a broad provider-superiority claim.

## Source runs

| Run | Model used here | Config | Artefacts |
| --- | --- | --- | --- |
| `leaderboard_claude_haiku_all_envs_direct_20` | `claude-haiku-4-5-20251001` | `configs/leaderboard/leaderboard_claude_haiku_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_claude_haiku_all_envs_direct_20/` |
| `leaderboard_openai_frontier_all_envs_direct_20` | `gpt-5.4` completed row only | `configs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20/` |

Both rows use agent `direct`, cache enabled, `max_workers=1`, run seed `123`,
environment seed `123`, `max_tokens=512`, no tools, no reflective agent, and no
robustness variants. The task set is 20 tasks each for `bayesian_games`,
`auctions`, `hidden_regimes`, `market_making`, `prediction_markets`, and
`adversarial_risk`.

Claude Haiku 4.5 used provider `anthropic`, API model ID
`claude-haiku-4-5-20251001`, and `temperature=0`. The model ID and pricing were
checked against Anthropic's current model documentation:
`https://platform.claude.com/docs/en/about-claude/models/all-models`.

## Cost gate

The pre-run estimate for the Claude Haiku config was `$0.364` upper bound for
120 direct calls, below the `$1.00` stop line. The observed estimated cost from
saved usage metadata was `$0.158726`.

## Overall comparison

Delta is Claude Haiku 4.5 minus OpenAI `gpt-5.4`. Higher score and pass rate are
better; lower parse failure, error, risk violation, latency, and cost are better.

| Metric | Claude Haiku 4.5 | OpenAI `gpt-5.4` | Delta |
| --- | ---: | ---: | ---: |
| Mean score | 0.509641 | 0.662963 | -0.153322 |
| Pass rate | 0.216667 | 0.425000 | -0.208333 |
| Parse failure rate | 0.000000 | 0.000000 | +0.000000 |
| Runtime error rate | 0.000000 | 0.000000 | +0.000000 |
| Provider error rate | 0.000000 | 0.000000 | +0.000000 |
| Risk violation rate | 0.125000 | 0.033333 | +0.091667 |
| Latency p50 (ms) | 1959.981 | 2356.810 | -396.829 |
| Latency p95 (ms) | 3843.240 | 3622.971 | +220.269 |
| Observed estimated cost | `$0.158726` | `$0.326270` | `-$0.167544` |

Saved usage totals:

| Model | Input tokens | Output tokens | Total tokens | Observed estimated cost |
| --- | ---: | ---: | ---: | ---: |
| Claude Haiku 4.5 | 59,691 | 19,807 | 79,498 | `$0.158726` |
| OpenAI `gpt-5.4` | 54,781 | 12,622 | 67,403 | `$0.326270` |

## Per-environment mean scores

Delta is Claude Haiku 4.5 minus OpenAI `gpt-5.4`.

| Environment | Claude Haiku 4.5 | OpenAI `gpt-5.4` | Delta |
| --- | ---: | ---: | ---: |
| `adversarial_risk` | 0.453500 | 0.850000 | -0.396500 |
| `auctions` | 0.036949 | 0.193458 | -0.156509 |
| `bayesian_games` | 0.769154 | 0.883559 | -0.114405 |
| `hidden_regimes` | 0.675455 | 0.848995 | -0.173540 |
| `market_making` | 0.581961 | 0.772774 | -0.190813 |
| `prediction_markets` | 0.540825 | 0.428989 | +0.111835 |

## Preliminary reading

Claude Haiku 4.5 completed all 120 calls with zero parse failures and zero
provider/runtime errors. In this small direct-agent slice, it was cheaper than
`gpt-5.4` and had lower p50 latency, but higher p95 latency, lower overall mean
score, lower pass rate, and a higher risk-violation rate.

The one environment where Claude Haiku 4.5 scored higher was
`prediction_markets` (`+0.111835`). Its largest deficits were in
`adversarial_risk` (`-0.396500`), `market_making` (`-0.190813`), and
`hidden_regimes` (`-0.173540`). `auctions` remained low-scoring for both rows,
with Claude lower on this task slice.

This should be read as a budget-conscious first Claude datapoint, not a provider
ranking. It covers one Claude model, one OpenAI comparison row, direct agents
only, synthetic deterministic tasks, 20 tasks per environment, no tools, no
robustness, and no reflective agents.
