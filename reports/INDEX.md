# MimirBench report index

Generated from saved artefacts. Reference, mock, and reference-tool runs are non-model diagnostics; real-model rows are only present when an actual run directory exists.

## Baseline runs

| Name | Path | Label | Tasks | Mean score / drop |
| --- | --- | --- | ---: | ---: |
| adversarial_risk_mock_smoke | `runs/adversarial_risk_mock_smoke` | mock diagnostic baseline | 50 | 0.424423 |
| adversarial_risk_reference_smoke | `runs/adversarial_risk_reference_smoke` | reference sanity check | 50 | 1 |
| all_envs_mock_smoke | `runs/all_envs_mock_smoke` | mock diagnostic baseline | 300 | 0.472748 |
| all_envs_reference_smoke | `runs/all_envs_reference_smoke` | reference sanity check | 300 | 0.999862 |
| auctions_reference_smoke | `runs/auctions_reference_smoke` | reference sanity check | 100 | 1 |
| bayes_mock_smoke | `runs/bayes_mock_smoke` | mock diagnostic baseline | 100 | 0.686737 |
| bayes_reference_smoke | `runs/bayes_reference_smoke` | reference sanity check | 100 | 1 |
| hidden_regimes_reference_smoke | `runs/hidden_regimes_reference_smoke` | reference sanity check | 100 | 1 |
| market_making_mock_smoke | `runs/market_making_mock_smoke` | mock diagnostic baseline | 50 | 0.596485 |
| market_making_reference_smoke | `runs/market_making_reference_smoke` | reference sanity check | 50 | 0.99905 |
| prediction_markets_mock_smoke | `runs/prediction_markets_mock_smoke` | mock diagnostic baseline | 50 | 0.244629 |
| prediction_markets_reference_smoke | `runs/prediction_markets_reference_smoke` | reference sanity check | 50 | 1 |
| small_transformer_bayes_eval | `runs/small_transformer_bayes_eval` | unknown | n/a | n/a |
| tool_reference_bayes | `runs/tool_reference_bayes` | deterministic non-model tool baseline | 10 | 1 |

## Robustness runs

| Name | Path | Label | Tasks | Mean score / drop |
| --- | --- | --- | ---: | ---: |
| robustness_mock_all_envs | `runs/robustness_mock_all_envs` | mock agent (diagnostic baseline) | 90 | 0.00548605 |
| robustness_mock_bayes | `runs/robustness_mock_bayes` | mock agent (diagnostic baseline) | 25 | 0.0949578 |
| robustness_reference_all_envs | `runs/robustness_reference_all_envs` | reference solver (sanity check) | 90 | 1.32169e-18 |
| robustness_reference_bayes | `runs/robustness_reference_bayes` | reference solver (sanity check) | 25 | 7.10543e-18 |

## Comparison runs

| Name | Path | Label | Tasks | Mean score / drop |
| --- | --- | --- | ---: | ---: |
| mock_bayes | `runs/comparisons/mock_bayes` | reference sanity check | 20 | n/a |
| reference_bayes | `runs/comparisons/reference_bayes` | reference sanity check | 20 | n/a |
| tool_reference_bayes | `runs/comparisons/tool_reference_bayes` | reference sanity check | 20 | n/a |

## Interpretability runs

| Name | Path | Status | Experiments | Action probe acc |
| --- | --- | --- | --- | ---: |
| interp_bayes_all_tiny | `interpretability/interp_bayes_all_tiny` | complete | probes, activation_patching, attention_analysis | 0.916667 |
| interp_bayes_attention_tiny | `interpretability/interp_bayes_attention_tiny` | complete | attention_analysis | n/a |
| interp_bayes_patching_tiny | `interpretability/interp_bayes_patching_tiny` | complete | activation_patching | n/a |
| interp_bayes_probes_tiny | `interpretability/interp_bayes_probes_tiny` | complete | probes | 0.916667 |

Interpretability runs analyse a small synthetic Bayesian transformer. Probe accuracy is decodability, not causation; no frontier-model claim is made.

## Model cards

- `model_cards/agent_source.md`
- `model_cards/cli_train.md`
- `model_cards/eval_source.md`
- `model_cards/mock_bayes_mock_random_valid__mock_random_valid.md`
- `model_cards/reference_bayes_reference__reference.md`
- `model_cards/small_transformer_bayes_tiny.md`
- `model_cards/test_tiny.md`
- `model_cards/tool_reference_bayes_tool_reference__tool_reference.md`

## Generated figures

- `interpretability/interp_bayes_all_tiny/activation_patching/figures/action_recovery_by_layer.png`
- `interpretability/interp_bayes_all_tiny/activation_patching/figures/causal_effect_by_layer.png`
- `interpretability/interp_bayes_all_tiny/activation_patching/figures/label_recovery_by_layer.png`
- `interpretability/interp_bayes_all_tiny/attention/figures/attention_entropy_by_layer.png`
- `interpretability/interp_bayes_all_tiny/attention/figures/evidence_attention_by_layer.png`
- `interpretability/interp_bayes_all_tiny/attention/figures/prior_attention_by_layer.png`
- `interpretability/interp_bayes_all_tiny/probes/figures/action_probe_accuracy_by_layer.png`
- `interpretability/interp_bayes_all_tiny/probes/figures/confidence_probe_accuracy_by_layer.png`
- `interpretability/interp_bayes_all_tiny/probes/figures/posterior_probe_accuracy_by_layer.png`
- `interpretability/interp_bayes_all_tiny/probes/figures/risk_probe_accuracy_by_layer.png`
- `interpretability/interp_bayes_attention_tiny/attention/figures/attention_entropy_by_layer.png`
- `interpretability/interp_bayes_attention_tiny/attention/figures/evidence_attention_by_layer.png`
- `interpretability/interp_bayes_attention_tiny/attention/figures/prior_attention_by_layer.png`
- `interpretability/interp_bayes_patching_tiny/activation_patching/figures/action_recovery_by_layer.png`
- `interpretability/interp_bayes_patching_tiny/activation_patching/figures/causal_effect_by_layer.png`
- `interpretability/interp_bayes_patching_tiny/activation_patching/figures/label_recovery_by_layer.png`
- `interpretability/interp_bayes_probes_tiny/probes/figures/action_probe_accuracy_by_layer.png`
- `interpretability/interp_bayes_probes_tiny/probes/figures/confidence_probe_accuracy_by_layer.png`
- `interpretability/interp_bayes_probes_tiny/probes/figures/posterior_probe_accuracy_by_layer.png`
- `interpretability/interp_bayes_probes_tiny/probes/figures/risk_probe_accuracy_by_layer.png`
- `runs/comparisons/mock_bayes/figures/latency_distribution.png`
- `runs/comparisons/mock_bayes/figures/parse_failure_rate_by_agent.png`
- `runs/comparisons/mock_bayes/figures/posterior_error_distribution.png`
- `runs/comparisons/mock_bayes/figures/risk_violation_rate_by_environment.png`
- `runs/comparisons/mock_bayes/figures/score_by_environment.png`
- `runs/comparisons/reference_bayes/figures/latency_distribution.png`
- `runs/comparisons/reference_bayes/figures/parse_failure_rate_by_agent.png`
- `runs/comparisons/reference_bayes/figures/posterior_error_distribution.png`
- `runs/comparisons/reference_bayes/figures/risk_violation_rate_by_environment.png`
- `runs/comparisons/reference_bayes/figures/score_by_environment.png`
- `runs/comparisons/tool_reference_bayes/figures/latency_distribution.png`
- `runs/comparisons/tool_reference_bayes/figures/parse_failure_rate_by_agent.png`
- `runs/comparisons/tool_reference_bayes/figures/posterior_error_distribution.png`
- `runs/comparisons/tool_reference_bayes/figures/risk_violation_rate_by_environment.png`
- `runs/comparisons/tool_reference_bayes/figures/score_by_environment.png`
- `runs/small_transformer_bayes_eval/figures/posterior_abs_error.png`
- `runs/small_transformer_bayes_eval/figures/regret.png`
- `training/small_transformer_bayes_tiny/figures/training_loss.png`
- `training/small_transformer_bayes_tiny/figures/validation_accuracy.png`
- `training/small_transformer_bayes_tiny/figures/validation_posterior_bucket_accuracy.png`
- `training/small_transformer_bayes_tiny/figures/validation_risk_accuracy.png`

## Caveats

- All entries are backed by files under `reports/`.
- Do not treat reference, mock, or deterministic tool baselines as real model results.
- Do not describe any result as evidence of trading ability, trading usefulness, or profitability.
- Real API/local model reports remain pending unless actual run artefacts exist.
