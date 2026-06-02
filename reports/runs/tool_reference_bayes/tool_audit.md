# Tool-use audit: tool_reference_bayes

- Agent: `tool::reference::bayesian_games`
- Tasks with tool audit: `10`

## Metrics

- tool_call_rate: `1`
- invalid_tool_call_rate: `0`
- tool_error_rate: `0`
- mean_tool_steps: `1`
- final_answer_after_tool_rate: `1`
- tool_result_ignored_rate: `0`

`tool_result_ignored_rate` and `final_answer_used_tool_result` are deterministic numeric-overlap heuristics; `unknown`/`null` means the heuristic could not decide.

## Example tool steps

| task | step | tool | status | error | used_result |
| --- | ---: | --- | --- | --- | --- |
| `bayesian_games-123` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-124` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-125` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-126` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-127` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-128` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-129` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-130` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-131` | 1 | `bayes_calculator` | allowed |  | yes |
| `bayesian_games-132` | 1 | `bayes_calculator` | allowed |  | yes |
