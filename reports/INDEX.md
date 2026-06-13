# MimirBench report index

Index of saved evaluation artefacts. Reference, mock, and reference-tool runs are non-model controls; hosted-model rows are present only when a completed run directory exists.

## Baseline runs

| Name | Path | Label | Tasks | Mean score / drop |
| --- | --- | --- | ---: | ---: |
| adversarial_risk_mock_smoke | [`runs/adversarial_risk_mock_smoke`](runs/adversarial_risk_mock_smoke) | mock diagnostic baseline | 50 | 0.424423 |
| adversarial_risk_reference_smoke | [`runs/adversarial_risk_reference_smoke`](runs/adversarial_risk_reference_smoke) | reference sanity check | 50 | 1 |
| all_envs_mock_smoke | [`runs/all_envs_mock_smoke`](runs/all_envs_mock_smoke) | mock diagnostic baseline | 300 | 0.472748 |
| all_envs_reference_smoke | [`runs/all_envs_reference_smoke`](runs/all_envs_reference_smoke) | reference sanity check | 300 | 0.999862 |
| auctions_reference_smoke | [`runs/auctions_reference_smoke`](runs/auctions_reference_smoke) | reference sanity check | 100 | 1 |
| bayes_mock_smoke | [`runs/bayes_mock_smoke`](runs/bayes_mock_smoke) | mock diagnostic baseline | 100 | 0.686737 |
| bayes_reference_smoke | [`runs/bayes_reference_smoke`](runs/bayes_reference_smoke) | reference sanity check | 100 | 1 |
| full_scale_mock_validation | [`runs/full_scale_mock_validation`](runs/full_scale_mock_validation) | mock diagnostic baseline | 6000 | 0.455064 |
| full_scale_reference_validation | [`runs/full_scale_reference_validation`](runs/full_scale_reference_validation) | reference sanity check | 6000 | 0.999862 |
| hidden_regimes_reference_smoke | [`runs/hidden_regimes_reference_smoke`](runs/hidden_regimes_reference_smoke) | reference sanity check | 100 | 1 |
| market_making_mock_smoke | [`runs/market_making_mock_smoke`](runs/market_making_mock_smoke) | mock diagnostic baseline | 50 | 0.596485 |
| market_making_reference_smoke | [`runs/market_making_reference_smoke`](runs/market_making_reference_smoke) | reference sanity check | 50 | 0.99905 |
| prediction_markets_mock_smoke | [`runs/prediction_markets_mock_smoke`](runs/prediction_markets_mock_smoke) | mock diagnostic baseline | 50 | 0.244629 |
| prediction_markets_reference_smoke | [`runs/prediction_markets_reference_smoke`](runs/prediction_markets_reference_smoke) | reference sanity check | 50 | 1 |
| small_transformer_bayes_eval | [`runs/small_transformer_bayes_eval`](runs/small_transformer_bayes_eval) | unknown | n/a | n/a |
| small_transformer_bayes_medium_eval | [`runs/small_transformer_bayes_medium_eval`](runs/small_transformer_bayes_medium_eval) | unknown | n/a | n/a |
| tool_reference_bayes | [`runs/tool_reference_bayes`](runs/tool_reference_bayes) | deterministic non-model tool baseline | 10 | 1 |
| verify_require_tool_bayes_micro | [`runs/verify_require_tool_bayes_micro`](runs/verify_require_tool_bayes_micro) | hosted API model | 3 | 0.619711 |
| verify_require_tool_bayes_micro_v2 | [`runs/verify_require_tool_bayes_micro_v2`](runs/verify_require_tool_bayes_micro_v2) | hosted API model | 3 | 0.999637 |
| verify_require_tool_predmkt_micro | [`runs/verify_require_tool_predmkt_micro`](runs/verify_require_tool_predmkt_micro) | hosted API model | 3 | 0.237347 |

## Robustness runs

| Name | Path | Label | Tasks | Mean score / drop |
| --- | --- | --- | ---: | ---: |
| leaderboard_claude_sonnet_robustness_tiny | [`runs/leaderboard/leaderboard_claude_sonnet_robustness_tiny`](runs/leaderboard/leaderboard_claude_sonnet_robustness_tiny) | hosted model | 18 | -0.00529801 |
| leaderboard_gemini_pro_robustness_small | [`runs/leaderboard/leaderboard_gemini_pro_robustness_small`](runs/leaderboard/leaderboard_gemini_pro_robustness_small) | hosted model | 18 | -0.0124366 |
| leaderboard_gemini_strongest_robustness_tiny | [`runs/leaderboard/leaderboard_gemini_strongest_robustness_tiny`](runs/leaderboard/leaderboard_gemini_strongest_robustness_tiny) | hosted model | 30 | 0.0280413 |
| leaderboard_openai_gpt54_robustness_tiny | [`runs/leaderboard/leaderboard_openai_gpt54_robustness_tiny`](runs/leaderboard/leaderboard_openai_gpt54_robustness_tiny) | hosted model | 30 | 0.0484097 |
| robustness_mock_all_envs | [`runs/robustness_mock_all_envs`](runs/robustness_mock_all_envs) | mock agent (diagnostic baseline) | 90 | 0.00548605 |
| robustness_mock_bayes | [`runs/robustness_mock_bayes`](runs/robustness_mock_bayes) | mock agent (diagnostic baseline) | 25 | 0.0949578 |
| robustness_reference_all_envs | [`runs/robustness_reference_all_envs`](runs/robustness_reference_all_envs) | reference solver (sanity check) | 90 | 1.32169e-18 |
| robustness_reference_bayes | [`runs/robustness_reference_bayes`](runs/robustness_reference_bayes) | reference solver (sanity check) | 25 | 7.10543e-18 |

## Comparison runs

| Name | Path | Label | Tasks | Mean score / drop |
| --- | --- | --- | ---: | ---: |
| mock_bayes | [`runs/comparisons/mock_bayes`](runs/comparisons/mock_bayes) | reference sanity check | 20 | n/a |
| reference_bayes | [`runs/comparisons/reference_bayes`](runs/comparisons/reference_bayes) | reference sanity check | 20 | n/a |
| tool_reference_bayes | [`runs/comparisons/tool_reference_bayes`](runs/comparisons/tool_reference_bayes) | reference sanity check | 20 | n/a |

## Leaderboard runs

| Name | Path | Models run | Pending | Tasks/agent | Headlines | Pilot-scale |
| --- | --- | ---: | ---: | ---: | ---: | :---: |
| leaderboard_all_available_tiny | [`runs/leaderboard/leaderboard_all_available_tiny`](runs/leaderboard/leaderboard_all_available_tiny) | 0 | 3 | 60 | 0 | yes |
| leaderboard_claude_haiku_all_envs_direct_20 | [`runs/leaderboard/leaderboard_claude_haiku_all_envs_direct_20`](runs/leaderboard/leaderboard_claude_haiku_all_envs_direct_20) | 1 | 0 | 120 | 0 | yes |
| leaderboard_claude_sonnet_all_envs_direct_20 | [`runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20`](runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20) | 1 | 0 | 120 | 0 | yes |
| leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536 | [`runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536`](runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536) | 1 | 0 | 120 | 0 | yes |
| leaderboard_claude_sonnet_rescue_probe_1024 | [`runs/leaderboard/leaderboard_claude_sonnet_rescue_probe_1024`](runs/leaderboard/leaderboard_claude_sonnet_rescue_probe_1024) | 1 | 0 | 30 | 0 | yes |
| leaderboard_gemini_flash_all_envs_direct_20 | [`runs/leaderboard/leaderboard_gemini_flash_all_envs_direct_20`](runs/leaderboard/leaderboard_gemini_flash_all_envs_direct_20) | 1 | 0 | 120 | 0 | yes |
| leaderboard_gemini_flash_all_envs_direct_20_thinking0 | [`runs/leaderboard/leaderboard_gemini_flash_all_envs_direct_20_thinking0`](runs/leaderboard/leaderboard_gemini_flash_all_envs_direct_20_thinking0) | 1 | 0 | 120 | 0 | yes |
| leaderboard_gemini_flash_lite_all_envs_direct_20 | [`runs/leaderboard/leaderboard_gemini_flash_lite_all_envs_direct_20`](runs/leaderboard/leaderboard_gemini_flash_lite_all_envs_direct_20) | 1 | 0 | 120 | 0 | yes |
| leaderboard_gemini_flash_lite_smoke | [`runs/leaderboard/leaderboard_gemini_flash_lite_smoke`](runs/leaderboard/leaderboard_gemini_flash_lite_smoke) | 1 | 0 | 6 | 0 | yes |
| leaderboard_gemini_flash_rescue_probe_thinking0 | [`runs/leaderboard/leaderboard_gemini_flash_rescue_probe_thinking0`](runs/leaderboard/leaderboard_gemini_flash_rescue_probe_thinking0) | 1 | 0 | 6 | 0 | yes |
| leaderboard_gemini_pro_all_envs_direct_20 | [`runs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20`](runs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20) | 1 | 0 | 120 | 0 | yes |
| leaderboard_gemini_pro_all_envs_direct_20_retry | [`runs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20_retry`](runs/leaderboard/leaderboard_gemini_pro_all_envs_direct_20_retry) | 1 | 0 | 120 | 0 | yes |
| leaderboard_gemini_pro_rescue_probe_low_thinking | [`runs/leaderboard/leaderboard_gemini_pro_rescue_probe_low_thinking`](runs/leaderboard/leaderboard_gemini_pro_rescue_probe_low_thinking) | 1 | 0 | 6 | 0 | yes |
| leaderboard_gemini_pro_smoke | [`runs/leaderboard/leaderboard_gemini_pro_smoke`](runs/leaderboard/leaderboard_gemini_pro_smoke) | 1 | 0 | 6 | 0 | yes |
| leaderboard_openai_all_envs_direct_tiny | [`runs/leaderboard/leaderboard_openai_all_envs_direct_tiny`](runs/leaderboard/leaderboard_openai_all_envs_direct_tiny) | 1 | 0 | 30 | 0 | yes |
| leaderboard_openai_bayes_direct_20 | [`runs/leaderboard/leaderboard_openai_bayes_direct_20`](runs/leaderboard/leaderboard_openai_bayes_direct_20) | 1 | 0 | 20 | 0 | yes |
| leaderboard_openai_bayes_direct_micro | [`runs/leaderboard/leaderboard_openai_bayes_direct_micro`](runs/leaderboard/leaderboard_openai_bayes_direct_micro) | 1 | 0 | 5 | 0 | yes |
| leaderboard_openai_frontier_all_envs_direct_20 | [`runs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20`](runs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20) | 2 | 0 | 120 | 0 | yes |
| leaderboard_openai_gpt54mini_bayes_direct_tool_50 | [`runs/leaderboard/leaderboard_openai_gpt54mini_bayes_direct_tool_50`](runs/leaderboard/leaderboard_openai_gpt54mini_bayes_direct_tool_50) | 1 | 0 | 50 | 0 | no |
| leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25 | [`runs/leaderboard/leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25`](runs/leaderboard/leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25) | 1 | 0 | 50 | 0 | no |
| leaderboard_openai_gpt55_all_envs_direct_20 | [`runs/leaderboard/leaderboard_openai_gpt55_all_envs_direct_20`](runs/leaderboard/leaderboard_openai_gpt55_all_envs_direct_20) | 1 | 0 | 120 | 0 | yes |
| leaderboard_openai_gpt55_rescue_probe | [`runs/leaderboard/leaderboard_openai_gpt55_rescue_probe`](runs/leaderboard/leaderboard_openai_gpt55_rescue_probe) | 1 | 0 | 6 | 0 | yes |
| leaderboard_openai_minis_all_envs_direct_20 | [`runs/leaderboard/leaderboard_openai_minis_all_envs_direct_20`](runs/leaderboard/leaderboard_openai_minis_all_envs_direct_20) | 2 | 0 | 120 | 0 | yes |
| leaderboard_openai_modern_mini_all_envs_direct_tiny | [`runs/leaderboard/leaderboard_openai_modern_mini_all_envs_direct_tiny`](runs/leaderboard/leaderboard_openai_modern_mini_all_envs_direct_tiny) | 1 | 0 | 30 | 0 | yes |

Leaderboard rows are hosted/local-model results only when `models_run > 0` and the saved summary contains concrete per-agent run artefacts.

## Hosted-Model Row Classification

Tracks follow [BENCHMARK_PROTOCOL.md](../BENCHMARK_PROTOCOL.md). Only `strict-track clean` and `best-valid clean` rows are headline comparisons; everything else is a documented protocol/probe/diagnostic artefact.

| Leaderboard run | Track / classification |
| --- | --- |
| `leaderboard_all_available_tiny` | reference/mock/non-model status check (no model run) |
| `leaderboard_claude_haiku_all_envs_direct_20` | strict-track clean |
| `leaderboard_claude_sonnet_all_envs_direct_20` | protocol-limited (max_tokens=512 truncation) |
| `leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536` | best-valid clean (max_tokens=1536) |
| `leaderboard_claude_sonnet_rescue_probe_1024` | rescue probe (30 tasks, max_tokens=1024) |
| `leaderboard_gemini_flash_all_envs_direct_20` | protocol-limited (default thinking, 512 budget) |
| `leaderboard_gemini_flash_all_envs_direct_20_thinking0` | best-valid clean (thinking_budget=0) |
| `leaderboard_gemini_flash_lite_all_envs_direct_20` | strict-track clean |
| `leaderboard_gemini_flash_lite_smoke` | smoke run (6 tasks) |
| `leaderboard_gemini_flash_rescue_probe_thinking0` | rescue probe (6 tasks, thinking disabled) |
| `leaderboard_gemini_pro_all_envs_direct_20` | provider-failed diagnostic (14/120 503/504) |
| `leaderboard_gemini_pro_all_envs_direct_20_retry` | best-valid clean (cache-backed; provider-load condition) |
| `leaderboard_gemini_pro_rescue_probe_low_thinking` | rescue probe (6 tasks, thinking_level=low) |
| `leaderboard_gemini_pro_smoke` | smoke run (request rejected, no model usage) |
| `leaderboard_openai_all_envs_direct_tiny` | smoke run (30 tasks) |
| `leaderboard_openai_bayes_direct_20` | smoke run (single-environment) |
| `leaderboard_openai_bayes_direct_micro` | smoke run (5 tasks) |
| `leaderboard_openai_frontier_all_envs_direct_20` | strict-track clean (gpt-5.4); protocol-limited (gpt-5.5) |
| `leaderboard_openai_gpt54mini_bayes_direct_tool_50` | diagnostic forced-tool run (direct vs tool) |
| `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25` | diagnostic forced-tool run (direct vs tool) |
| `leaderboard_openai_gpt55_all_envs_direct_20` | protocol-limited (default temp, 512 budget) |
| `leaderboard_openai_gpt55_rescue_probe` | rescue probe (6 tasks, raised budget) |
| `leaderboard_openai_minis_all_envs_direct_20` | strict-track clean (gpt-4.1-mini, gpt-5.4-mini) |
| `leaderboard_openai_modern_mini_all_envs_direct_tiny` | smoke run (30 tasks) |

## Standalone leaderboard analysis notes

- [`runs/leaderboard/claude_model_ladder_direct_20env_comparison.md`](runs/leaderboard/claude_model_ladder_direct_20env_comparison.md)
- [`runs/leaderboard/cross_provider_direct_20env_comparison.md`](runs/leaderboard/cross_provider_direct_20env_comparison.md)
- [`runs/leaderboard/full_benchmark_power_plan.md`](runs/leaderboard/full_benchmark_power_plan.md)
- [`runs/leaderboard/gemini_budget_extension_attempts.md`](runs/leaderboard/gemini_budget_extension_attempts.md)
- [`runs/leaderboard/gemini_model_ladder_direct_20env_comparison.md`](runs/leaderboard/gemini_model_ladder_direct_20env_comparison.md)
- [`runs/leaderboard/gemini_strongest_robustness_comparison.md`](runs/leaderboard/gemini_strongest_robustness_comparison.md)
- [`runs/leaderboard/openai_model_ladder_20env_comparison.md`](runs/leaderboard/openai_model_ladder_20env_comparison.md)
- [`runs/leaderboard/statistical_validity_existing_artifacts.md`](runs/leaderboard/statistical_validity_existing_artifacts.md)

## Full benchmark planning manifests

- [`plans/leaderboard_best_valid_100env_3seeds.json`](plans/leaderboard_best_valid_100env_3seeds.json)
- [`plans/leaderboard_best_valid_200env_5seeds.json`](plans/leaderboard_best_valid_200env_5seeds.json)
- [`plans/leaderboard_strict_100env_3seeds.json`](plans/leaderboard_strict_100env_3seeds.json)
- [`plans/leaderboard_strict_200env_5seeds.json`](plans/leaderboard_strict_200env_5seeds.json)

## Interpretability runs

| Name | Path | Status | Experiments | Action probe acc |
| --- | --- | --- | --- | ---: |
| interp_bayes_all_medium | [`interpretability/interp_bayes_all_medium`](interpretability/interp_bayes_all_medium) | complete | probes, activation_patching, attention_analysis | 1 |
| interp_bayes_all_medium_seed_124 | [`interpretability/interp_bayes_all_medium_seed_124`](interpretability/interp_bayes_all_medium_seed_124) | complete | probes, activation_patching, attention_analysis | 1 |
| interp_bayes_all_medium_seed_125 | [`interpretability/interp_bayes_all_medium_seed_125`](interpretability/interp_bayes_all_medium_seed_125) | complete | probes, activation_patching, attention_analysis | 1 |
| interp_bayes_all_medium_seed_126 | [`interpretability/interp_bayes_all_medium_seed_126`](interpretability/interp_bayes_all_medium_seed_126) | complete | probes, activation_patching, attention_analysis | 1 |
| interp_bayes_all_medium_seed_127 | [`interpretability/interp_bayes_all_medium_seed_127`](interpretability/interp_bayes_all_medium_seed_127) | complete | probes, activation_patching, attention_analysis | 1 |
| interp_bayes_all_medium_seed_128 | [`interpretability/interp_bayes_all_medium_seed_128`](interpretability/interp_bayes_all_medium_seed_128) | complete | probes, activation_patching, attention_analysis | 1 |
| interp_bayes_all_tiny | [`interpretability/interp_bayes_all_tiny`](interpretability/interp_bayes_all_tiny) | complete | probes, activation_patching, attention_analysis | 0.916667 |
| interp_bayes_attention_tiny | [`interpretability/interp_bayes_attention_tiny`](interpretability/interp_bayes_attention_tiny) | complete | attention_analysis | n/a |
| interp_bayes_medium_extended | [`interpretability/interp_bayes_medium_extended`](interpretability/interp_bayes_medium_extended) | complete | n/a | n/a |
| interp_bayes_medium_extended_seed_124 | [`interpretability/interp_bayes_medium_extended_seed_124`](interpretability/interp_bayes_medium_extended_seed_124) | complete | n/a | n/a |
| interp_bayes_medium_extended_seed_125 | [`interpretability/interp_bayes_medium_extended_seed_125`](interpretability/interp_bayes_medium_extended_seed_125) | complete | n/a | n/a |
| interp_bayes_medium_extended_seed_126 | [`interpretability/interp_bayes_medium_extended_seed_126`](interpretability/interp_bayes_medium_extended_seed_126) | complete | n/a | n/a |
| interp_bayes_medium_extended_seed_127 | [`interpretability/interp_bayes_medium_extended_seed_127`](interpretability/interp_bayes_medium_extended_seed_127) | complete | n/a | n/a |
| interp_bayes_medium_extended_seed_128 | [`interpretability/interp_bayes_medium_extended_seed_128`](interpretability/interp_bayes_medium_extended_seed_128) | complete | n/a | n/a |
| interp_bayes_patching_tiny | [`interpretability/interp_bayes_patching_tiny`](interpretability/interp_bayes_patching_tiny) | complete | activation_patching | n/a |
| interp_bayes_probes_tiny | [`interpretability/interp_bayes_probes_tiny`](interpretability/interp_bayes_probes_tiny) | complete | probes | 0.916667 |

Interpretability runs analyse a small synthetic Bayesian transformer. Probe accuracy is decodability, not causation; no frontier-model claim is made.

## Model cards

- [`model_cards/mock_bayes_mock_random_valid__mock_random_valid.md`](model_cards/mock_bayes_mock_random_valid__mock_random_valid.md)
- [`model_cards/reference_bayes_reference__reference.md`](model_cards/reference_bayes_reference__reference.md)
- [`model_cards/small_transformer_bayes_medium.md`](model_cards/small_transformer_bayes_medium.md)
- [`model_cards/small_transformer_bayes_medium_ablation_data2k.md`](model_cards/small_transformer_bayes_medium_ablation_data2k.md)
- [`model_cards/small_transformer_bayes_tiny.md`](model_cards/small_transformer_bayes_tiny.md)
- [`model_cards/tool_reference_bayes_tool_reference__tool_reference.md`](model_cards/tool_reference_bayes_tool_reference__tool_reference.md)

## Generated figures

- [`interpretability/interp_bayes_all_medium/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_all_medium/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_all_medium/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_all_medium/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_all_medium/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_all_medium/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_all_medium/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_all_medium/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_all_medium/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium/probes/figures/risk_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_124/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_124/probes/figures/risk_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_125/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_125/probes/figures/risk_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_126/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_126/probes/figures/risk_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_127/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_127/probes/figures/risk_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_medium_seed_128/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_medium_seed_128/probes/figures/risk_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_all_tiny/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_all_tiny/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_all_tiny/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_all_tiny/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_all_tiny/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_all_tiny/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_tiny/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_tiny/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_tiny/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_all_tiny/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_all_tiny/probes/figures/risk_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_attention_tiny/attention/figures/attention_entropy_by_layer.png`](interpretability/interp_bayes_attention_tiny/attention/figures/attention_entropy_by_layer.png)
- [`interpretability/interp_bayes_attention_tiny/attention/figures/evidence_attention_by_layer.png`](interpretability/interp_bayes_attention_tiny/attention/figures/evidence_attention_by_layer.png)
- [`interpretability/interp_bayes_attention_tiny/attention/figures/prior_attention_by_layer.png`](interpretability/interp_bayes_attention_tiny/attention/figures/prior_attention_by_layer.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_123/figures/posterior_abs_error.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_123/figures/posterior_abs_error.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_123/figures/regret.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_123/figures/regret.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_124/figures/posterior_abs_error.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_124/figures/posterior_abs_error.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_124/figures/regret.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_124/figures/regret.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_125/figures/posterior_abs_error.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_125/figures/posterior_abs_error.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_125/figures/regret.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_125/figures/regret.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_126/figures/posterior_abs_error.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_126/figures/posterior_abs_error.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_126/figures/regret.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_126/figures/regret.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_127/figures/posterior_abs_error.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_127/figures/posterior_abs_error.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_127/figures/regret.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_127/figures/regret.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_128/figures/posterior_abs_error.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_128/figures/posterior_abs_error.png)
- [`interpretability/interp_bayes_multiseed/heldout_eval_seed_128/figures/regret.png`](interpretability/interp_bayes_multiseed/heldout_eval_seed_128/figures/regret.png)
- [`interpretability/interp_bayes_patching_tiny/activation_patching/figures/action_recovery_by_layer.png`](interpretability/interp_bayes_patching_tiny/activation_patching/figures/action_recovery_by_layer.png)
- [`interpretability/interp_bayes_patching_tiny/activation_patching/figures/causal_effect_by_layer.png`](interpretability/interp_bayes_patching_tiny/activation_patching/figures/causal_effect_by_layer.png)
- [`interpretability/interp_bayes_patching_tiny/activation_patching/figures/label_recovery_by_layer.png`](interpretability/interp_bayes_patching_tiny/activation_patching/figures/label_recovery_by_layer.png)
- [`interpretability/interp_bayes_probes_tiny/probes/figures/action_probe_accuracy_by_layer.png`](interpretability/interp_bayes_probes_tiny/probes/figures/action_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_probes_tiny/probes/figures/confidence_probe_accuracy_by_layer.png`](interpretability/interp_bayes_probes_tiny/probes/figures/confidence_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_probes_tiny/probes/figures/posterior_probe_accuracy_by_layer.png`](interpretability/interp_bayes_probes_tiny/probes/figures/posterior_probe_accuracy_by_layer.png)
- [`interpretability/interp_bayes_probes_tiny/probes/figures/risk_probe_accuracy_by_layer.png`](interpretability/interp_bayes_probes_tiny/probes/figures/risk_probe_accuracy_by_layer.png)
- [`runs/comparisons/mock_bayes/figures/latency_distribution.png`](runs/comparisons/mock_bayes/figures/latency_distribution.png)
- [`runs/comparisons/mock_bayes/figures/parse_failure_rate_by_agent.png`](runs/comparisons/mock_bayes/figures/parse_failure_rate_by_agent.png)
- [`runs/comparisons/mock_bayes/figures/posterior_error_distribution.png`](runs/comparisons/mock_bayes/figures/posterior_error_distribution.png)
- [`runs/comparisons/mock_bayes/figures/risk_violation_rate_by_environment.png`](runs/comparisons/mock_bayes/figures/risk_violation_rate_by_environment.png)
- [`runs/comparisons/mock_bayes/figures/score_by_environment.png`](runs/comparisons/mock_bayes/figures/score_by_environment.png)
- [`runs/comparisons/reference_bayes/figures/latency_distribution.png`](runs/comparisons/reference_bayes/figures/latency_distribution.png)
- [`runs/comparisons/reference_bayes/figures/parse_failure_rate_by_agent.png`](runs/comparisons/reference_bayes/figures/parse_failure_rate_by_agent.png)
- [`runs/comparisons/reference_bayes/figures/posterior_error_distribution.png`](runs/comparisons/reference_bayes/figures/posterior_error_distribution.png)
- [`runs/comparisons/reference_bayes/figures/risk_violation_rate_by_environment.png`](runs/comparisons/reference_bayes/figures/risk_violation_rate_by_environment.png)
- [`runs/comparisons/reference_bayes/figures/score_by_environment.png`](runs/comparisons/reference_bayes/figures/score_by_environment.png)
- [`runs/comparisons/tool_reference_bayes/figures/latency_distribution.png`](runs/comparisons/tool_reference_bayes/figures/latency_distribution.png)
- [`runs/comparisons/tool_reference_bayes/figures/parse_failure_rate_by_agent.png`](runs/comparisons/tool_reference_bayes/figures/parse_failure_rate_by_agent.png)
- [`runs/comparisons/tool_reference_bayes/figures/posterior_error_distribution.png`](runs/comparisons/tool_reference_bayes/figures/posterior_error_distribution.png)
- [`runs/comparisons/tool_reference_bayes/figures/risk_violation_rate_by_environment.png`](runs/comparisons/tool_reference_bayes/figures/risk_violation_rate_by_environment.png)
- [`runs/comparisons/tool_reference_bayes/figures/score_by_environment.png`](runs/comparisons/tool_reference_bayes/figures/score_by_environment.png)
- [`runs/small_transformer_bayes_eval/figures/posterior_abs_error.png`](runs/small_transformer_bayes_eval/figures/posterior_abs_error.png)
- [`runs/small_transformer_bayes_eval/figures/regret.png`](runs/small_transformer_bayes_eval/figures/regret.png)
- [`runs/small_transformer_bayes_medium_eval/figures/posterior_abs_error.png`](runs/small_transformer_bayes_medium_eval/figures/posterior_abs_error.png)
- [`runs/small_transformer_bayes_medium_eval/figures/regret.png`](runs/small_transformer_bayes_medium_eval/figures/regret.png)
- [`training/small_transformer_bayes_medium/figures/training_loss.png`](training/small_transformer_bayes_medium/figures/training_loss.png)
- [`training/small_transformer_bayes_medium/figures/validation_accuracy.png`](training/small_transformer_bayes_medium/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_medium/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_medium/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_medium/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_medium/figures/validation_risk_accuracy.png)
- [`training/small_transformer_bayes_medium_ablation_data2k/figures/training_loss.png`](training/small_transformer_bayes_medium_ablation_data2k/figures/training_loss.png)
- [`training/small_transformer_bayes_medium_ablation_data2k/figures/validation_accuracy.png`](training/small_transformer_bayes_medium_ablation_data2k/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_medium_ablation_data2k/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_medium_ablation_data2k/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_medium_ablation_data2k/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_medium_ablation_data2k/figures/validation_risk_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_124/figures/training_loss.png`](training/small_transformer_bayes_medium_seed_124/figures/training_loss.png)
- [`training/small_transformer_bayes_medium_seed_124/figures/validation_accuracy.png`](training/small_transformer_bayes_medium_seed_124/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_124/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_medium_seed_124/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_124/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_medium_seed_124/figures/validation_risk_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_125/figures/training_loss.png`](training/small_transformer_bayes_medium_seed_125/figures/training_loss.png)
- [`training/small_transformer_bayes_medium_seed_125/figures/validation_accuracy.png`](training/small_transformer_bayes_medium_seed_125/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_125/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_medium_seed_125/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_125/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_medium_seed_125/figures/validation_risk_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_126/figures/training_loss.png`](training/small_transformer_bayes_medium_seed_126/figures/training_loss.png)
- [`training/small_transformer_bayes_medium_seed_126/figures/validation_accuracy.png`](training/small_transformer_bayes_medium_seed_126/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_126/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_medium_seed_126/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_126/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_medium_seed_126/figures/validation_risk_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_127/figures/training_loss.png`](training/small_transformer_bayes_medium_seed_127/figures/training_loss.png)
- [`training/small_transformer_bayes_medium_seed_127/figures/validation_accuracy.png`](training/small_transformer_bayes_medium_seed_127/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_127/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_medium_seed_127/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_127/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_medium_seed_127/figures/validation_risk_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_128/figures/training_loss.png`](training/small_transformer_bayes_medium_seed_128/figures/training_loss.png)
- [`training/small_transformer_bayes_medium_seed_128/figures/validation_accuracy.png`](training/small_transformer_bayes_medium_seed_128/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_128/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_medium_seed_128/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_medium_seed_128/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_medium_seed_128/figures/validation_risk_accuracy.png)
- [`training/small_transformer_bayes_tiny/figures/training_loss.png`](training/small_transformer_bayes_tiny/figures/training_loss.png)
- [`training/small_transformer_bayes_tiny/figures/validation_accuracy.png`](training/small_transformer_bayes_tiny/figures/validation_accuracy.png)
- [`training/small_transformer_bayes_tiny/figures/validation_posterior_bucket_accuracy.png`](training/small_transformer_bayes_tiny/figures/validation_posterior_bucket_accuracy.png)
- [`training/small_transformer_bayes_tiny/figures/validation_risk_accuracy.png`](training/small_transformer_bayes_tiny/figures/validation_risk_accuracy.png)

## Scope and Limitations

- All entries are backed by files under `reports/`.
- Reference, mock, and deterministic tool baselines are non-model controls.
- Results do not establish trading ability, trading usefulness, or profitability.
- Hosted API/local model reports remain pending unless complete run artefacts exist.
- Full-scale reference/mock runs are infrastructure validations, not model capability results.
- Hosted-model full tracks are implemented and costed but remain unrun pending external budget.
