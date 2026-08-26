# Pilot Claude model-ladder comparison (direct, 20 tasks/env)

Generated from saved artefacts on 2026-06-03 local time. This is a synthetic,
direct-agent-only comparison with 20 tasks per environment across six
environments. It compares two Anthropic models (Claude Haiku 4.5 and Claude
Sonnet 4.6) against the completed OpenAI `gpt-5.4` direct row as an external
reference. It is **not** statistically conclusive, **not** a trading result, and
**not** a broad provider- or model-superiority claim.

## Source runs

| Run | Model used here | Config | Artefacts |
| --- | --- | --- | --- |
| `leaderboard_claude_haiku_all_envs_direct_20` | `claude-haiku-4-5-20251001` | `configs/leaderboard/leaderboard_claude_haiku_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_claude_haiku_all_envs_direct_20/` |
| `leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536` (clean) | `claude-sonnet-4-6` | `configs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536.yaml` | `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536/` |
| `leaderboard_claude_sonnet_all_envs_direct_20` (protocol-limited, max_tokens=512) | `claude-sonnet-4-6` | `configs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20/` |
| `leaderboard_openai_frontier_all_envs_direct_20` | `gpt-5.4` completed row only | `configs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20/` |

All rows use agent `direct`, cache enabled, `max_workers=1`, run seed `123`,
environment seed `123`, `temperature=0`, no tools, no reflective agent, and no
robustness variants. The task set is 20 tasks each for `bayesian_games`,
`auctions`, `hidden_regimes`, `market_making`, `prediction_markets`, and
`adversarial_risk`, with identical task IDs/seeds across all rows. Model IDs were
confirmed against the live Anthropic model list (`claude-sonnet-4-6` =
"Claude Sonnet 4.6"; `claude-haiku-4-5-20251001` = "Claude Haiku 4.5").

## Output-budget (max_tokens) protocol note: read before comparing

This is the most important caveat. The rows are **not** at an identical output
budget:

- Claude Haiku 4.5 and OpenAI `gpt-5.4` parsed cleanly at `max_tokens=512`
  (0% parse failures).
- Claude Sonnet 4.6 at the same `max_tokens=512` writes a long natural-language
  reasoning preamble before the JSON and was **truncated mid-output**
  (`finish_reason="max_tokens"`, `no_json_object`) on 70/120 tasks, giving a
  **59.2% parse-failure rate** and a depressed mean score of `0.368856`. That run
  is retained as a documented protocol-limited finding, not a capability score.
- A rescue probe at `max_tokens=1024` (30 tasks) dropped Sonnet's parse-failure
  rate to 6.7% and raised mean score to `0.816447`, confirming the failures were
  output-budget truncation, not capability. Measured output need: mean 538
  tokens/call, p90 1013, with a tail above 1024.
- The clean Sonnet row used here therefore uses `max_tokens=1536`. This is a
  genuine protocol difference: Sonnet's row reflects "score when given enough
  output budget to finish," while Haiku/`gpt-5.4` were already clean at 512. Treat
  Sonnet-vs-others comparisons as across each model's clean protocol, not as a
  strictly identical-decoding comparison. (This mirrors the `gpt-5.5`
  default-temperature caveat in the OpenAI ladder.)

Even at `max_tokens=1536`, Sonnet still had 3/120 residual truncations, **all in
`auctions`** (its most verbose derivations); those 3 score 0 and pull the
`auctions` mean down from ~1.0 (on the 17 parsed) to `0.849957`.

## Cost gate and observed spend

| Run | Pre-run upper estimate | Observed estimated cost |
| --- | ---: | ---: |
| Claude Haiku 4.5 (512) | `$0.364000` | `$0.158726` |
| Claude Sonnet 4.6 (512, protocol-limited) | `$1.092` | `$0.906528` |
| Claude Sonnet 4.6 rescue probe (1024, 30 tasks) | `$0.5034` | `$0.286554` |
| Claude Sonnet 4.6 (1536, clean) | `$2.9352` | `$1.233993` |
| OpenAI `gpt-5.4` (512) | already completed | `$0.326270` |

The clean Sonnet run's upper estimate (`$2.9352`) exceeds the usual `$2.00`
single-run gate because the estimator uses `max_tokens x tasks` as the output
upper bound; the observed cost (`$1.233993`) was 42% of that bound. The run was
explicitly authorized on that basis.

## Overall comparison (clean rows)

Higher mean score and pass rate are better; lower parse failure, error, risk
violation, latency, and cost are better.

| Metric | Claude Haiku 4.5 | Claude Sonnet 4.6 (clean) | OpenAI `gpt-5.4` |
| --- | ---: | ---: | ---: |
| Output budget (`max_tokens`) | 512 | 1536 | 512 |
| Mean score | 0.509641 | 0.856713 | 0.662963 |
| Pass rate | 0.216667 | 0.783333 | 0.425000 |
| Parse failure rate | 0.000000 | 0.025000 | 0.000000 |
| Provider/runtime error rate | 0.000000 | 0.000000 | 0.000000 |
| Risk-limit violation rate | 0.125000 | 0.000000 | 0.033333 |
| Latency p50 (ms) | 1959.981 | 9820.486 | 2356.810 |
| Latency p95 (ms) | 3843.240 | 19766.327 | 3622.971 |
| Observed estimated cost | `$0.158726` | `$1.233993` | `$0.326270` |

Saved usage totals:

| Model | Input tokens | Output tokens | Total tokens | Observed estimated cost |
| --- | ---: | ---: | ---: | ---: |
| Claude Haiku 4.5 | 59,691 | 19,807 | 79,498 | `$0.158726` |
| Claude Sonnet 4.6 (clean, 1536) | 59,811 | 70,304 | 130,115 | `$1.233993` |
| OpenAI `gpt-5.4` | 54,781 | 12,622 | 67,403 | `$0.326270` |

Sonnet's much larger output-token count (70,304 vs Haiku 19,807, `gpt-5.4`
12,622) reflects its verbose reasoning style; its higher cost is driven by both
that verbosity and the higher Sonnet per-token price ($3/$15 per 1M vs Haiku
$1/$5).

## Per-environment mean scores

| Environment | Claude Haiku 4.5 | Claude Sonnet 4.6 (clean) | OpenAI `gpt-5.4` |
| --- | ---: | ---: | ---: |
| `adversarial_risk` | 0.453500 | 0.835000 | 0.850000 |
| `auctions` | 0.036949 | 0.849957 | 0.193458 |
| `bayesian_games` | 0.769154 | 0.999425 | 0.883559 |
| `hidden_regimes` | 0.675455 | 0.994175 | 0.848995 |
| `market_making` | 0.581961 | 0.809274 | 0.772774 |
| `prediction_markets` | 0.540825 | 0.652447 | 0.428989 |

(`auctions` for Sonnet is held down by 3 residual truncations; the 17 parsed
tasks scored ~1.0, so Sonnet's untruncated `auctions` capability is higher than
the `0.849957` shown.)

## Sonnet 4.6 (clean) minus Claude Haiku 4.5

| Metric / environment | Delta (Sonnet - Haiku) |
| --- | ---: |
| Mean score | +0.347072 |
| Pass rate | +0.566666 |
| Parse failure rate | +0.025000 |
| Risk-limit violation rate | -0.125000 |
| `adversarial_risk` | +0.381500 |
| `auctions` | +0.813008 |
| `bayesian_games` | +0.230271 |
| `hidden_regimes` | +0.318720 |
| `market_making` | +0.227313 |
| `prediction_markets` | +0.111622 |

Sonnet scored higher than Haiku in every environment and had zero risk-limit
violations (vs Haiku's 0.125), at the cost of much higher latency and ~7.8x the
spend, plus a small parse-failure rate concentrated in `auctions`.

## Sonnet 4.6 (clean) minus OpenAI `gpt-5.4`

| Metric / environment | Delta (Sonnet - gpt-5.4) |
| --- | ---: |
| Mean score | +0.193750 |
| Pass rate | +0.358333 |
| Parse failure rate | +0.025000 |
| Risk-limit violation rate | -0.033333 |
| `adversarial_risk` | -0.015000 |
| `auctions` | +0.656499 |
| `bayesian_games` | +0.115866 |
| `hidden_regimes` | +0.145180 |
| `market_making` | +0.036500 |
| `prediction_markets` | +0.223458 |

Against the external `gpt-5.4` reference (which used `max_tokens=512`), Sonnet at
`max_tokens=1536` scored higher overall and in five of six environments, with
`adversarial_risk` essentially tied (`-0.015`), and had a lower risk-violation
rate. It was also far slower and more expensive, and unlike `gpt-5.4` it required
the larger output budget to parse cleanly.

## Pilot reading

- The strongest **clean** Claude direct row in this benchmark snapshot is
  **Claude Sonnet 4.6** (`claude-sonnet-4-6`) at `max_tokens=1536`: mean score
  `0.856713`, pass rate `0.783333`, zero risk-limit violations, with a small
  (`0.025`) parse-failure rate confined to `auctions`.
- Claude Haiku 4.5 is the strongest clean Claude row at the original
  `max_tokens=512` protocol, but scores well below Sonnet and `gpt-5.4` and has
  the highest risk-violation rate of the three.
- On these synthetic tasks Sonnet 4.6 outscored the `gpt-5.4` reference overall
  and in most environments, but at a strong latency and cost penalty and only
  after its output budget was tripled to avoid truncation.
- This is a budget-conscious, pilot comparison: one Anthropic ladder
  (two models) plus one external OpenAI reference row, direct agents only,
  synthetic deterministic tasks, 20 tasks per environment, one seed/task
  schedule, no tools, no reflective agents, and a non-identical output budget for
  Sonnet. The sample does not establish broad provider superiority or real-world
  performance.
