# Gemini model ladder direct comparison (20/env)

Updated 2026-06-03 after the cache-backed Pro retry and small Pro robustness
probe. This compares completed Gemini direct-agent rows against the strongest
completed OpenAI direct row (`gpt-5.4`) and the strongest clean Claude direct row
(Claude Sonnet 4.6 at `max_tokens=1536`). It is preliminary, synthetic,
direct-agent only, and not statistically conclusive.

## Sources and protocol

| Row | Model ID | Config | Artefacts |
| --- | --- | --- | --- |
| Gemini Flash-Lite | `gemini-3.1-flash-lite` | `configs/leaderboard/leaderboard_gemini_flash_lite_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_gemini_flash_lite_all_envs_direct_20/` |
| Gemini Flash clean | `gemini-3.5-flash` | `configs/leaderboard/leaderboard_gemini_flash_all_envs_direct_20_thinking0.yaml` | `reports/runs/leaderboard/leaderboard_gemini_flash_all_envs_direct_20_thinking0/` |
| Gemini Pro diagnostic | `gemini-3.1-pro-preview` | `configs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20/` |
| Gemini Pro clean retry | `gemini-3.1-pro-preview` | `configs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20_retry.yaml` | `reports/runs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20_retry/` |
| Gemini Pro robustness | `gemini-3.1-pro-preview` | `configs/leaderboard/leaderboard_gemini_pro_robustness_small.yaml` | `reports/runs/leaderboard/leaderboard_gemini_pro_robustness_small/` |
| OpenAI reference | `gpt-5.4` | `configs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20/` |
| Claude reference | `claude-sonnet-4-6` | `configs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536.yaml` | `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536/` |

All 20/env rows use direct agent only, no tools, no reflective agent, six
environments, 20 tasks/environment, seed `123`, cache enabled, and
`max_workers=1`.

Official Google docs and the Gemini SDK model listing confirmed
`models/gemini-3.1-pro-preview` on 2026-06-03. The Pro smoke using
`thinking_budget=0` was rejected because Gemini 3 Pro only works in thinking
mode, so clean Pro rows use `thinking_level=low` and `max_tokens=4096`.

## Cost gates and observed cost

| Run | Pre-run upper estimate | Observed / incremental cost | Outcome |
| --- | ---: | ---: | --- |
| Flash-Lite smoke (6 tasks) | `$0.0053` | `$0.001661` | clean |
| Flash-Lite 20/env | `$0.1064` | `$0.036121` | clean enough |
| Flash default-thinking 20/env | `$0.6382` | `$0.636148` | protocol-limited |
| Flash thinking-disabled rescue probe | `$0.0319` | `$0.011357` | clean |
| Flash clean 20/env (`thinking_budget=0`) | `$0.6382` | `$0.228205` | clean |
| Gemini Flash robustness | manual `~$0.75` | bounded `~$0.75` | complete |
| Pro smoke (`thinking_budget=0`) | `$0.0794` | not estimated | request rejected before model usage |
| Pro rescue probe (`thinking_level=low`) | `$0.3006` | `$0.048754` | clean |
| Pro 20/env diagnostic | `$6.0118` | `$1.130186` | unclean, 14 provider errors |
| Pro cache-backed 20/env retry | `$6.0118` full-row; cache-adjusted `~$0.35` | `$0.046798` incremental; merged row `$1.313882` | clean, 113 cache hits + 7 new calls |
| Pro robustness small | `$3.6071` | `$0.757786` | complete, 18 base + 54 variants |
| Flash 100/env expansion | `$3.1908` | no completed summary | stopped under provider load |

Using the prior bounded Gemini spend baseline of about `GBP 2.27`, the Pro retry
and Pro robustness added about `GBP 0.64`, giving updated bounded Gemini spend of
about `GBP 2.91` and remaining budget of about `GBP 7.09`. This remains below
the requested `GBP 9.25` stop line.

## Main direct results

| Row | Tasks | Mean score | Pass rate | Parse failure | Provider/runtime error | Risk violation | Latency p50/p95 ms | Observed row cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini Flash-Lite | 120 | 0.653520 | 0.400000 | 0.016667 | 0.000000 | 0.041667 | 736.3 / 904.6 | `$0.036121` |
| Gemini Flash clean (`thinking_budget=0`) | 120 | 0.745386 | 0.441667 | 0.008333 | 0.000000 | 0.008333 | 1573.4 / 1985.4 | `$0.228205` |
| Gemini Pro clean retry (`thinking_level=low`) | 120 | 0.854475 | 0.783333 | 0.000000 | 0.000000 | 0.000000 | 8589.6 / 51159.0 | `$1.313882` |
| OpenAI `gpt-5.4` | 120 | 0.662963 | 0.425000 | 0.000000 | 0.000000 | 0.033333 | 2356.8 / 3623.0 | `$0.326270` |
| Claude Sonnet 4.6 (clean, 1536) | 120 | 0.856713 | 0.783333 | 0.025000 | 0.000000 | 0.000000 | 9820.5 / 19766.3 | `$1.233993` |

The initial Pro diagnostic is still a provider-load diagnostic: it completed
106/120 model calls and failed 14 tasks after retries (3 `503 UNAVAILABLE` and
11 `504 DEADLINE_EXCEEDED`). The clean Pro retry reused 113 cached successful
responses, made only 7 new Gemini calls, and completed the same 120 task
IDs/seeds with zero provider/runtime errors and zero parse failures.

## Per-environment mean scores

| Environment | Flash-Lite | Flash clean | Pro clean retry | OpenAI `gpt-5.4` | Claude Sonnet 4.6 |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 0.800000 | 0.880000 | 0.850000 | 0.850000 | 0.835000 |
| auctions | 0.197183 | 0.495045 | 0.999997 | 0.193458 | 0.849957 |
| bayesian_games | 0.806853 | 0.860836 | 0.999481 | 0.883559 | 0.999425 |
| hidden_regimes | 0.867870 | 0.871691 | 0.977005 | 0.848995 | 0.994175 |
| market_making | 0.657497 | 0.782985 | 0.664517 | 0.772774 | 0.809274 |
| prediction_markets | 0.591715 | 0.581761 | 0.635853 | 0.428989 | 0.652447 |

## Deltas

Flash clean minus Flash-Lite: mean score `+0.091866`, pass rate `+0.041667`,
parse failure `-0.008333`, risk violation `-0.033333`, cost `+$0.192084`.

Pro clean retry minus Flash clean: mean score `+0.109089`, pass rate
`+0.341667`, parse failure `-0.008333`, provider/runtime error `+0.000000`, risk
violation `-0.008333`, cost `+$1.085677`, latency p50/p95
`+7016.1/+49173.7 ms`. Environment deltas: adversarial_risk `-0.030000`,
auctions `+0.504952`, bayesian_games `+0.138646`, hidden_regimes `+0.105314`,
market_making `-0.118468`, prediction_markets `+0.054092`.

Pro clean retry minus OpenAI `gpt-5.4`: mean score `+0.191513`, pass rate
`+0.358333`, parse failure `+0.000000`, provider/runtime error `+0.000000`, risk
violation `-0.033333`, cost `+$0.987612`, latency p50/p95
`+6232.8/+47536.1 ms`. This is a paired synthetic comparison only, not a broad
provider claim.

Pro clean retry minus Claude Sonnet 4.6: mean score `-0.002238`, pass rate
`+0.000000`, parse failure `-0.025000`, provider/runtime error `+0.000000`, risk
violation `+0.000000`, cost `+$0.079889`, latency p50/p95
`-1230.9/+31392.7 ms`. This is not a broad head-to-head ranking.

## Pro robustness

The small Pro robustness run used 18 base tasks and 54 deterministic variants
with the same direct Pro settings (`thinking_level=low`, `max_tokens=4096`,
cache enabled, `max_workers=1`). It completed with 72 cache rows, no provider
errors, and estimated incremental cost `$0.757786`.

| Metric | Gemini Pro clean retry |
| --- | ---: |
| Base tasks / variants | 18 / 54 |
| Paraphrase consistency | 0.833333 |
| Action flip rate | 0.166667 |
| Mean score drop | -0.012437 |
| Worst score drop | 0.368997 |
| Unsafe action increase | 0.000000 |
| Risk violation increase | 0.000000 |
| Pressure susceptibility | 0.190162 |
| Invalid response increase | 0.000000 |
| Distractor robustness | 0.833333 |

The negative mean score drop means variants scored slightly higher on average
than their base tasks in this small synthetic sample. It is not a significance
claim.

## Strongest clean Gemini row

The strongest clean Gemini direct row in this snapshot is now **Gemini Pro
Preview `gemini-3.1-pro-preview` with `thinking_level=low`**, mean score
`0.854475`, pass rate `0.783333`, parse-failure rate `0.000000`, and
provider/runtime error rate `0.000000`. Report it with the provider-load caveat:
the first full Pro attempt failed 14/120 tasks under 503/504 load and the clean
row required a cache-backed retry.

Gemini Flash `gemini-3.5-flash` with `thinking_budget=0` remains the strongest
clean non-Pro Gemini row and the row used for the earlier larger Gemini
robustness probe.

## Caveats

These are synthetic deterministic tasks with one task schedule and 20
tasks/environment for the main ladder. They are direct-agent results only, not
tool-use or reflective-agent results. They are preliminary and not statistically
conclusive. They are not trading results. No broad provider-superiority claim is
made. The initial Pro diagnostic remains provider-failed and is not a capability
row; the clean Pro retry is a cache-backed row under provider-load caveats.
Protocol-limited rows and provider-error rows must not be used for capability
claims.
