# Tool-use audit: verify_require_tool_predmkt_micro

- Agent: `tool::openai::gpt-5.4-mini`
- Tasks with tool audit: `3`

## Metrics

- tool_call_rate: `1`
- invalid_tool_call_rate: `0`
- tool_error_rate: `0`
- mean_tool_steps: `1`
- final_answer_after_tool_rate: `1`
- tool_result_ignored_rate: `0.3333`

`tool_result_ignored_rate` and `final_answer_used_tool_result` are deterministic numeric-overlap heuristics; `unknown`/`null` means the heuristic could not decide.

## Example tool steps

| task | step | tool | status | error | used_result |
| --- | ---: | --- | --- | --- | --- |
| `prediction_markets-123` | 1 | `bayes_calculator` | allowed |  | yes |
| `prediction_markets-124` | 1 | `bayes_calculator` | allowed |  | yes |
| `prediction_markets-125` | 1 | `bayes_calculator` | allowed |  | no |
