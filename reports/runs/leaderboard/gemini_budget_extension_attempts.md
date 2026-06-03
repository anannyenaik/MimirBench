# Gemini budget extension attempts

Updated 2026-06-03. Goal: spend remaining Gemini budget on high-value
additional evidence while keeping `max_workers=1`, cache enabled, and cumulative
observed-plus-bounded spend below the requested `GBP 9.25` stop line.

## Completed evidence

| Step | Config | Estimate | Observed / incremental cost | Outcome |
| --- | --- | ---: | ---: | --- |
| Pro smoke | `configs/leaderboard/leaderboard_gemini_pro_smoke.yaml` | `$0.0794` | not estimated | `thinking_budget=0` rejected: Pro only works in thinking mode |
| Pro rescue probe | `configs/leaderboard/leaderboard_gemini_pro_rescue_probe_low_thinking.yaml` | `$0.3006` | `$0.048754` | clean, 6/6 parsed |
| Pro 20/env diagnostic | `configs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20.yaml` | `$6.0118` | `$1.130186` | not clean: 14/120 provider errors |
| Cache-backed Pro retry | `configs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20_retry.yaml` | `$6.0118` full-row upper; cache-adjusted `~$0.35` | `$0.046798` incremental | clean merged row: 113 cache hits, 7 new calls, 0 provider/parse errors |
| Pro robustness small | `configs/leaderboard/leaderboard_gemini_pro_robustness_small.yaml` | `$3.6071` | `$0.757786` | complete: 18 base + 54 variants, 0 cache/provider errors |

The clean Pro retry row is saved at
`reports/runs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20_retry/`.
It has mean score `0.854475`, pass rate `0.783333`, parse-failure rate
`0.000000`, provider/runtime error rate `0.000000`, and risk-violation rate
`0.000000` over the same 120 task IDs/seeds as the initial Pro diagnostic.

The Pro robustness run is saved at
`reports/runs/leaderboard/leaderboard_gemini_pro_robustness_small/`. Its headline
metrics are paraphrase consistency `0.833333`, action flip rate `0.166667`, mean
score drop `-0.012437`, worst score drop `0.368997`, pressure susceptibility
`0.190162`, and unsafe/risk increase `0.000000`.

## Stopped attempts

| Attempt | Config | Estimate | Stop reason / later use |
| --- | --- | ---: | --- |
| Earlier Pro provider-error retry | `configs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20_retry_errors.yaml` | `$6.0118` | stopped under provider load; its local cache later contributed 7 successful responses to the clean retry cache |
| Cache-backed Flash 100/env expansion | `configs/leaderboard/leaderboard_gemini_flash_all_envs_direct_100_thinking0.yaml` | `$3.1908` | stopped under provider load; no completed leaderboard summary |

## Budget state

The prior bounded Gemini spend baseline was about `GBP 2.27`. The clean Pro retry
added `$0.046798` (`~GBP 0.037` at `$1 ~= GBP 0.80`). The Pro robustness run
added `$0.757786` (`~GBP 0.606`). Updated bounded Gemini spend is therefore
about `GBP 2.91`, leaving about `GBP 7.09` of a `GBP 10` cap and staying well
below the `GBP 9.25` stop line.

Gemini balance has now been used for the highest-value retry evidence: Pro moved
from provider-failed diagnostic to a clean cache-backed 20/env row, and a small
Pro robustness probe was added. Further spend is possible within the cap, but was
not needed for this controlled retry pass.

## Caveats

No statistical-significance claim is made. No trading-usefulness claim is made.
No broad provider-superiority claim is made. The initial Pro diagnostic remains a
provider-load diagnostic; the clean Pro retry should be reported with the caveat
that it required cache-backed retry after earlier 503/504 failures.
Protocol-limited rows and provider-failed rows are not capability rows.
