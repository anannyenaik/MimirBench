# Full benchmark power plan

**These are planning estimates based on pilot variance, not results from unrun hosted-model evaluations.**

The table uses each saved pilot row's task-level score variance and the normal approximation `total 95% CI width ~= 2 x 1.96 x pilot_sd / sqrt(n)`. It assumes iid task-level scaling. The current single-seed pilot cannot estimate seed-to-seed variation, so the full-run intervals may be wider than these planning values.

| Model | Pilot n | Pilot mean | Pilot SD | 20/env x 1 seed | 100/env x 3 seeds | 200/env x 5 seeds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenAI gpt-4.1-mini | 120 | 0.6196 | 0.3224 | 0.1154 | 0.0298 | 0.0163 |
| OpenAI gpt-5.4-mini | 120 | 0.6114 | 0.3429 | 0.1227 | 0.0317 | 0.0174 |
| OpenAI gpt-5.4 | 120 | 0.6630 | 0.3378 | 0.1209 | 0.0312 | 0.0171 |
| Claude Haiku 4.5 | 120 | 0.5096 | 0.3619 | 0.1295 | 0.0334 | 0.0183 |
| Claude Sonnet 4.6 (1536) | 120 | 0.8567 | 0.2130 | 0.0762 | 0.0197 | 0.0108 |
| Gemini Flash-Lite | 120 | 0.6535 | 0.3520 | 0.1260 | 0.0325 | 0.0178 |
| Gemini Flash (thinking_budget=0) | 120 | 0.7454 | 0.2715 | 0.0972 | 0.0251 | 0.0137 |
| Gemini Pro Preview (thinking_level=low, retry) | 120 | 0.8545 | 0.2010 | 0.0719 | 0.0186 | 0.0102 |

## Interpretation

- Widths are approximate total interval widths, not half-widths and not achieved results.
- Full tracks must report seed-level means and seed-to-seed variation directly; this pilot-derived calculation cannot substitute for those observations.
- Synthetic tasks, track-specific decoding, and row-classification caveats still apply.
- No provider-superiority or statistical-significance claim follows from this plan.
