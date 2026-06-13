# Gemini robustness comparison

Updated 2026-06-03. The first Gemini robustness probe ran on Gemini Flash
(`gemini-3.5-flash` with `thinking_budget=0`), which was then the strongest clean
Gemini direct row. After a cache-backed Pro retry produced a clean Pro 20/env
row, a smaller Pro robustness probe was added under the same direct Pro settings
(`thinking_level=low`, `max_tokens=4096`).

## Protocol

| Provider row | Model ID | Base tasks | Variants | Config | Artefacts |
| --- | --- | ---: | ---: | --- | --- |
| Gemini Flash | `gemini-3.5-flash` | 30 | 90 | `configs/leaderboard/leaderboard_gemini_strongest_robustness_tiny.yaml` | `reports/runs/leaderboard/leaderboard_gemini_strongest_robustness_tiny/` |
| Gemini Pro clean retry | `gemini-3.1-pro-preview` | 18 | 54 | `configs/leaderboard/leaderboard_gemini_pro_robustness_small.yaml` | `reports/runs/leaderboard/leaderboard_gemini_pro_robustness_small/` |
| OpenAI `gpt-5.4` reference | `gpt-5.4` | 30 | 90 | `configs/leaderboard/leaderboard_openai_gpt54_robustness_tiny.yaml` | `reports/runs/leaderboard/leaderboard_openai_gpt54_robustness_tiny/` |
| Claude Sonnet 4.6 reference | `claude-sonnet-4-6` | 18 | 54 | `configs/leaderboard/leaderboard_claude_sonnet_robustness_tiny.yaml` | `reports/runs/leaderboard/leaderboard_claude_sonnet_robustness_tiny/` |

All rows are direct agent only, no tools, no reflective agent, and use the same
variant taxonomy (`paraphrase`, `irrelevant_context`, `risk_pressure`). The
Gemini Pro robustness row is smaller than the Flash/OpenAI rows by design: it was
the first Pro robustness gate after provider failures were resolved by a
cache-backed retry.

## Overall metrics

| Metric | Gemini Flash | Gemini Pro | OpenAI `gpt-5.4` | Claude Sonnet 4.6 |
| --- | ---: | ---: | ---: | ---: |
| Base tasks / variants | 30 / 90 | 18 / 54 | 30 / 90 | 18 / 54 |
| Paraphrase consistency | 0.833333 | 0.833333 | 0.766667 | 1.000000 |
| Action flip rate | 0.133333 | 0.166667 | 0.188889 | 0.055556 |
| Mean score drop | 0.028041 | -0.012437 | 0.048410 | -0.005298 |
| Worst score drop | 0.998501 | 0.368997 | 0.999333 | 0.775142 |
| Unsafe action increase | 0.033333 | 0.000000 | 0.044444 | 0.018519 |
| Risk violation increase | 0.033333 | 0.000000 | 0.044444 | 0.018519 |
| Pressure susceptibility | 0.115308 | 0.190162 | 0.231500 | 0.120839 |
| Invalid response increase | 0.022222 | 0.000000 | 0.000000 | 0.000000 |
| Distractor robustness | 0.866667 | 0.833333 | 0.833333 | 0.944444 |

## Gemini failure concentration

Flash robustness failures were concentrated in `prediction_markets` (mean score
drop `0.104986`, risk increase `0.200000`) and `auctions` (action flip rate
`0.533333`, worst drop `0.998501`).

Pro robustness had no unsafe/risk increase and no invalid-response increase in
this small run. Its largest mean score drop was in `market_making` (`0.052738`),
and its highest action flip rate was in `auctions` (`0.666667`). The overall
mean score drop was negative (`-0.012437`), meaning variants scored slightly
higher than base tasks on average in this small synthetic sample.

## Cautious reading

The Pro robustness probe is useful because it tests the newly clean Pro row after
the provider-error retry, but it is small and should not be compared as a strict
ranking against the 30+90 Flash/OpenAI rows. These are pilot synthetic
diagnostics only. No statistical-significance, trading-usefulness, or broad
provider-superiority claim is made.
