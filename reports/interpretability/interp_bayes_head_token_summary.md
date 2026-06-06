# Per-head and individual-token interpretability summary

- Seeds attempted: [123, 124, 125, 126, 127, 128]
- Seeds completed: [123, 124, 125, 126, 127, 128]
- Local-only analysis; no hosted inference or API calls.

**Interpretation:** The six-seed attention-sub-block story is confirmed but refined: causal recovery is not localised to one consistently dominant head or individual position. Per-head ablation indicates distributed necessity, while single-head and single-position patches are usually insufficient. This does not support a clean circuit claim.

## Per-head patching

| Head site | Matched action recovery mean [range] | Posterior recovery | Action causal effect | Mismatched action recovery |
| --- | ---: | ---: | ---: | ---: |
| `blocks.0.attn_heads.0.out` | 0.056 [0.000, 0.239] | 0.000 [0.000, 0.000] | 0.052 [-0.000, 0.218] | 0.049 [0.000, 0.171] |
| `blocks.0.attn_heads.1.out` | 0.106 [0.000, 0.571] | 0.001 [0.000, 0.008] | 0.104 [-0.000, 0.565] | 0.069 [0.000, 0.333] |
| `blocks.0.attn_heads.2.out` | 0.007 [0.000, 0.026] | 0.000 [0.000, 0.000] | 0.007 [-0.000, 0.023] | 0.019 [0.008, 0.026] |
| `blocks.0.attn_heads.3.out` | 0.103 [0.000, 0.492] | 0.009 [0.000, 0.055] | 0.096 [0.003, 0.467] | 0.062 [0.008, 0.238] |
| `blocks.1.attn_heads.0.out` | 0.015 [0.000, 0.048] | 0.000 [0.000, 0.000] | 0.013 [-0.000, 0.039] | 0.016 [0.000, 0.063] |
| `blocks.1.attn_heads.1.out` | 0.113 [0.000, 0.615] | 0.014 [0.000, 0.078] | 0.110 [-0.000, 0.584] | 0.064 [0.000, 0.287] |
| `blocks.1.attn_heads.2.out` | 0.115 [0.000, 0.623] | 0.052 [0.000, 0.312] | 0.113 [-0.000, 0.613] | 0.070 [0.000, 0.344] |
| `blocks.1.attn_heads.3.out` | 0.141 [0.000, 0.532] | 0.038 [0.000, 0.195] | 0.135 [0.000, 0.502] | 0.096 [0.000, 0.310] |

## Per-head zero ablation

| Head site | Action accuracy degradation | Posterior accuracy degradation | Posterior error increase | Random-position action degradation |
| --- | ---: | ---: | ---: | ---: |
| `blocks.0.attn_heads.0.out` | 0.038 [0.000, 0.086] | 0.292 [0.141, 0.492] | 0.037 [0.013, 0.063] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_heads.1.out` | 0.031 [0.000, 0.070] | 0.217 [0.000, 0.648] | 0.027 [0.000, 0.073] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_heads.2.out` | 0.014 [0.000, 0.047] | 0.111 [0.023, 0.195] | 0.015 [0.001, 0.033] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_heads.3.out` | 0.051 [0.000, 0.094] | 0.314 [0.062, 0.703] | 0.045 [0.006, 0.104] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_heads.0.out` | 0.020 [0.000, 0.070] | 0.137 [0.000, 0.320] | 0.010 [0.000, 0.029] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_heads.1.out` | 0.016 [0.008, 0.031] | 0.142 [0.031, 0.281] | 0.014 [0.004, 0.035] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_heads.2.out` | 0.001 [0.000, 0.008] | 0.085 [0.000, 0.438] | 0.010 [-0.000, 0.050] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_heads.3.out` | 0.009 [0.000, 0.031] | 0.129 [0.000, 0.328] | 0.014 [0.000, 0.037] | 0.000 [0.000, 0.000] |

## Individual token-position patching

| Site | Max action recovery across positions | Mean action recovery | Max posterior recovery | Mean posterior recovery |
| --- | ---: | ---: | ---: | ---: |
| `blocks.0.attn_out` | 0.001 | 0.000 | 0.000 | 0.000 |
| `blocks.1.attn_out` | 0.000 | 0.000 | 0.000 | 0.000 |

The table shows the 20 strongest individual positions after every position was tested separately. Semantic aggregation below was computed only afterwards.

| Site | Position | Common token | Action recovery | Posterior recovery |
| --- | ---: | --- | ---: | ---: |
| `blocks.0.attn_out` | 25 | `not_X` | 0.001 [0.000, 0.009] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 45 | `=` | 0.001 [0.000, 0.009] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 0 | `<bos>` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 1 | `prior` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 2 | `A` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 3 | `=` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 4 | `0.500` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 5 | `B` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 6 | `=` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 7 | `0.500` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 8 | `;` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 9 | `likelihood` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 10 | `X` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 11 | `|` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 12 | `A` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 13 | `=` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 14 | `0.750` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 15 | `not_X` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 16 | `|` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | 17 | `A` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Post-hoc semantic aggregates and controls

| Site | Semantic group | Action recovery | Posterior recovery |
| --- | --- | ---: | ---: |
| `blocks.0.attn_out` | evidence | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | likelihood | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | payoff_risk | 0.000 [0.000, 0.001] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | prior | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.0.attn_out` | unclassified | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_out` | evidence | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_out` | likelihood | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_out` | payoff_risk | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_out` | prior | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| `blocks.1.attn_out` | unclassified | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |

## Limitations

- One narrow synthetic Bayesian/risk generator and one compact encoder architecture.
- Per-head sites are projected head contributions; they do not isolate neurons or features.
- Individual-position effects are measured before semantic aggregation and may be diluted by mean pooling.
- Zero ablation can move activations off distribution.
- No sparse-autoencoder or neuron-level analysis was performed.
- Nothing here transfers to frontier-model internals.
