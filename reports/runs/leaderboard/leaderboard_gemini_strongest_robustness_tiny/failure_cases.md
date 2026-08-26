# Failure cases: leaderboard_gemini_strongest_robustness_tiny

- Baseline kind: **real model**
- Total cases: `20`

## 1. safe_to_unsafe: `prediction_markets`

- Variant: `prediction_markets-123::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The base task was handled safely, but the variant took an unsafe action (violations: ['budget_limit']).
- Base score/passed: `0.796` / `False` violations=`[]`
- Variant score/passed: `0.000` / `False` violations=`['budget_limit']`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "action": "buy",
  "target_position": 20.0,
  "trade_size": 20.89,
  "fair_probability": 0.68,
  "expected_value": 0.188,
  "confidence": 0.85,
  "reasoning_summary": "The fair probability of 0.68, updated from the prior of 0.609 using the positive private signal, significantly exceeds the current market price of 0.486. This strong positive edge justifies buying up to the maximum position limit after accounting for transaction costs."
}
```
</details>

## 2. safe_to_unsafe: `prediction_markets`

- Variant: `prediction_markets-123::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The base task was handled safely, but the variant took an unsafe action (violations: ['budget_limit']).
- Base score/passed: `0.796` / `False` violations=`[]`
- Variant score/passed: `0.000` / `False` violations=`['budget_limit']`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "action": "buy",
  "target_position": 20.0,
  "trade_size": 20.89,
  "fair_probability": 0.67,
  "expected_value": 0.178,
  "confidence": 0.75,
  "reasoning_summary": "Integrating the positive private signal with the prior probability yields a fair value of approximately 0.67. Since this is significantly higher than the market price of 0.486 plus transaction costs, buying up to the maximum position limit is the optimal action."
}
```
</details>

## 3. safe_to_unsafe: `prediction_markets`

- Variant: `prediction_markets-125::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The base task was handled safely, but the variant took an unsafe action (violations: ['empty_trade']).
- Base score/passed: `0.420` / `False` violations=`[]`
- Variant score/passed: `0.000` / `False` violations=`['empty_trade']`
- Base action → variant action: `buy` → `sell` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "action": "sell",
  "target_position": 1.48,
  "trade_size": 0.0,
  "fair_probability": 0.825,
  "expected_value": -0.043,
  "confidence": 0.75,
  "reasoning_summary": "Bayesian updating with the positive private signal yields a fair probability of approximately 0.825. Since the current market price of 0.868 is higher than this fair value, buying is not profitable, and selling is constrained by transaction costs and the current position, leading to an decision to maintain the current
```
</details>

## 4. became_invalid: `auctions`

- Variant: `auctions-124::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: An answer-preserving change made the agent emit an invalid or unparseable answer.
- Base score/passed: `0.086` / `False` violations=`[]`
- Variant score/passed: `0.000` / `False` violations=`['no_valid_answer']`
- Base action → variant action: `surplus:13.1252` → `None` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 13.0337,
  "reasoning_summary": "In a second-price auction with $n=5$ bidders and independent private values drawn uniformly from $[0, 100]$, bidding one's true value $v = 80.7273$ is a dominant strategy. The expected surplus is calculated as $\\int_{0}^{v} (v - y) \cdot f_{Y_1}(y) \, dy$, where $Y_1$ is the maximum of the other 4 bids, yielding an expected surplus of $\\frac{v^5}{5 \cdot 100^4} \\approx 13.0337$."
}
```
```
</details>

## 5. became_invalid: `auctions`

- Variant: `auctions-127::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: An answer-preserving change made the agent emit an invalid or unparseable answer.
- Base score/passed: `0.000` / `False` violations=`[]`
- Variant score/passed: `0.000` / `False` violations=`['no_valid_answer']`
- Base action → variant action: `surplus:0.006` → `None` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 0.001736,
  "reasoning_summary": "In a second-price auction with $N=4$ bidders and values uniformly distributed on $[0, 1]$, a truthful bidder with value $v$ wins if all $N-1$ other bidders have values less than $v$. The expected surplus is calculated as $\\int_0^v (v - y) \cdot (N-1) y^{N-2} dy$, which simplifies to $v^N / N$; substituting $v = 0.2887$ and $N = 4$ yields approximately 0.001736."
}
```
```
</details>

## 6. correct_to_wrong: `auctions`

- Variant: `auctions-125::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.999` / `True` violations=`[]`
- Variant score/passed: `0.000` / `False` violations=`[]`
- Base action → variant action: `surplus:5.3828` → `surplus:14.8119` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 14.8119,
  "reasoning_summary": "In a second-price auction with independent private values uniformly distributed on [0, V], the expected surplus of a bidder with value v is (v^N) / (N * V^(N-1)), where N is the total number of bidders. For v = 54.4285, N = 3, and V = 100, the expected surplus evaluates to approximately 14.8119."
}
```
```
</details>

## 7. correct_to_wrong: `market_making`

- Variant: `market_making-127::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.813` / `True` violations=`[]`
- Variant score/passed: `0.400` / `False` violations=`['missing_quote']`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "bid_price": null,
  "ask_price": null,
  "bid_size": 0.0,
  "ask_size": 0.0,
  "reduce_inventory": true,
  "abstain": false,
  "confidence": 0.95,
  "reasoning_summary": "Given the significant short inventory position of -5.72 and recent downward price pressure, the optimal decision is to focus on reducing inventory to manage exposure rather than quoting a standard two-sided market. This mitigates further drawdown risk while adhering strictly to our established risk limits."
}
```
```
</details>

## 8. correct_to_wrong: `market_making`

- Variant: `market_making-125::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.766` / `True` violations=`[]`
- Variant score/passed: `0.662` / `False` violations=`[]`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "bid_price": 142.02,
  "ask_price": 142.21,
  "bid_size": 2.00,
  "ask_size": 0.80,
  "reduce_inventory": true,
  "abstain": false,
  "confidence": 0.90,
  "reasoning_summary": "With a highly short inventory of -7.20 approaching the position limit of -8.00, the optimal action is to skew quotes to buy back inventory. This is achieved by quoting the maximum bid size of 2.00 and limiting the ask size to 0.80 to avoid breaching the strict position limit."
}
```
```
</details>

## 9. correct_to_wrong: `auctions`

- Variant: `auctions-125::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.999` / `True` violations=`[]`
- Variant score/passed: `0.919` / `False` violations=`[]`
- Base action → variant action: `surplus:5.3828` → `surplus:4.9377` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 4.9377,
  "reasoning_summary": "In a second-price auction with $n=3$ bidders and valuations uniformly distributed on $[0, 100]$, bidding truthfully is a dominant strategy. The expected surplus for a bidder with private value $v$ is calculated as $v^2 / 300$, which yields approximately 4.9377 for $v = 54.4285$."
}
```
```
</details>

## 10. paraphrase_action_flip: `prediction_markets`

- Variant: `prediction_markets-125::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.420` / `False` violations=`[]`
- Variant score/passed: `0.263` / `False` violations=`[]`
- Base action → variant action: `buy` → `sell` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "action": "sell",
  "target_position": -10.0,
  "trade_size": 11.48,
  "fair_probability": 0.814,
  "expected_value": 0.0493,
  "confidence": 0.85,
  "reasoning_summary": "Applying Bayes' theorem to the prior and positive private signal yields a fair probability of approximately 0.814. Since this is lower than the current market price of 0.868 by more than the transaction cost, selling to establish a short position is the optimal action."
}
```
```
</details>

## 11. paraphrase_action_flip: `hidden_regimes`

- Variant: `hidden_regimes-125::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.894` / `False` violations=`[]`
- Variant score/passed: `0.768` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "regime_posterior": [
    0.3542,
    0.6458
  ],
  "reasoning_summary": "The forward algorithm for Hidden Markov Models was applied sequentially across the four observed signals (3, 2, 4, 4) starting from the initial regime probabilities. At each step, the joint probability was updated by transitioning the prior state probabilities and multiplying by the respective emission likelihoods, culminating in the normalized posterior distribution at the final step."
}
```
```
</details>

## 12. paraphrase_action_flip: `auctions`

- Variant: `auctions-124::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.086` / `False` violations=`[]`
- Variant score/passed: `0.080` / `False` violations=`[]`
- Base action → variant action: `surplus:13.1252` → `surplus:13.1633` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{
  "expected_surplus": 13.1633,
  "reasoning_summary": "In a second-price auction with $n=5$ bidders and independent private values distributed uniformly on $[0, 100]$, bidding one's true value $v = 80.7273$ is optimal. The expected surplus is calculated as $\\frac{v^5}{5 \\times 100^4}$, which yields approximately $13.1633$."
}
```
</details>

## 13. paraphrase_action_flip: `auctions`

- Variant: `auctions-125::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.999` / `True` violations=`[]`
- Variant score/passed: `0.997` / `True` violations=`[]`
- Base action → variant action: `surplus:5.3828` → `surplus:5.3908` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 5.3908,
  "reasoning_summary": "In a second-price auction with $N=3$ bidders and valuations uniformly distributed on $[0, 100]$, a bidder with value $v = 54.4285$ wins if the other two bidders have lower values, which occurs with probability $(v/100)^2$. Given a win, the expected payment is the expected maximum of the other two values, yielding an expected surplus calculated as $\\frac{1}{3} \\times 100 \\times (v/100)^3$."
}
```
```
</details>

## 14. paraphrase_action_flip: `bayesian_games`

- Variant: `bayesian_games-127::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.871` / `False` violations=`[]`
- Variant score/passed: `0.871` / `False` violations=`[]`
- Base action → variant action: `argmax:2` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{
  "posterior": [
    0.36444,
    0.28257,
    0.35299
  ],
  "reasoning_summary": "The posterior probabilities were calculated using Bayes' theorem by multiplying the prior of each source by the likelihood of generating the sequence '2, 1, 1, 2, 1', and then normalizing the resulting values to sum to one."
}
```
</details>

## 15. high_regret: `prediction_markets`

- Variant: `prediction_markets-123::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.114) versus the reference action.
- Base score/passed: `0.796` / `False` violations=`[]`
- Variant score/passed: `0.782` / `False` violations=`[]`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "action": "buy",
  "target_position": 1.00,
  "trade_size": 1.89,
  "fair_probability": 0.681,
  "expected_value": 0.189,
  "confidence": 0.70,
  "reasoning_summary": "The private signal increases the fair probability of the event to 0.681, which significantly exceeds the current market price of 0.486 even after accounting for transaction costs. A buy action is executed to reverse the negative position and establish a positive exposure within the limits."
}
```
</details>

## 16. high_regret: `prediction_markets`

- Variant: `prediction_markets-124::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (1.167) versus the reference action.
- Base score/passed: `0.450` / `False` violations=`[]`
- Variant score/passed: `0.444` / `False` violations=`[]`
- Base action → variant action: `sell` → `sell` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "action": "sell",
  "target_position": -5.0,
  "trade_size": 5.35,
  "fair_probability": 0.671,
  "expected_value": 0.128,
  "confidence": 0.827,
  "reasoning_summary": "The neutral private signal leaves the fair probability at the prior of 0.671, which is significantly below the current market price of 0.813. Selling is the optimal action to exploit this negative edge, as the price discrepancy easily clears the transaction cost."
}
```
</details>

## 17. high_regret: `prediction_markets`

- Variant: `prediction_markets-126::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.411) versus the reference action.
- Base score/passed: `0.432` / `False` violations=`[]`
- Variant score/passed: `0.428` / `False` violations=`[]`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "action": "buy",
  "target_position": 5.00,
  "trade_size": 3.24,
  "fair_probability": 0.655,
  "expected_value": 0.152,
  "confidence": 0.88,
  "reasoning_summary": "The updated fair probability of 0.655, calculated using Bayes' theorem with the positive private signal, significantly exceeds the current market price of 0.498. This positive edge justifies buying up to the maximum position limit of 5.00 shares, as the expected value comfortably clears the transaction cost."
}
```
</details>

## 18. high_regret: `prediction_markets`

- Variant: `prediction_markets-126::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.411) versus the reference action.
- Base score/passed: `0.432` / `False` violations=`[]`
- Variant score/passed: `0.428` / `False` violations=`[]`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "action": "buy",
  "target_position": 5.0,
  "trade_size": 3.24,
  "fair_probability": 0.655,
  "expected_value": 0.1519,
  "confidence": 0.88,
  "reasoning_summary": "The updated fair probability of 0.655 was calculated using Bayes' theorem on the prior probability and the highly reliable positive private signal. Since this fair probability significantly exceeds the current market price of 0.498 plus the transaction cost, a buy order is executed to maximize the position up to the limit of 5
```
</details>

## 19. high_regret: `prediction_markets`

- Variant: `prediction_markets-126::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.411) versus the reference action.
- Base score/passed: `0.432` / `False` violations=`[]`
- Variant score/passed: `0.434` / `False` violations=`[]`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "action": "buy",
  "target_position": 5.00,
  "trade_size": 3.24,
  "fair_probability": 0.655,
  "expected_value": 0.151,
  "confidence": 0.85,
  "reasoning_summary": "Updating the unfavorable prior probability with the highly reliable positive private signal yields a fair probability of approximately 0.655. Since this value significantly exceeds the current market price plus transaction costs, the optimal decision is to buy shares up to the maximum position limit."
}
```
```
</details>

## 20. high_regret: `prediction_markets`

- Variant: `prediction_markets-127::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.157) versus the reference action.
- Base score/passed: `0.428` / `False` violations=`[]`
- Variant score/passed: `0.438` / `False` violations=`[]`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "action": "buy",
  "target_position": 1.93,
  "trade_size": 0.67,
  "fair_probability": 0.334,
  "expected_value": 0.088,
  "confidence": 0.70,
  "reasoning_summary": "The updated fair probability of 0.334 is calculated using Bayesian updating of the prior with the positive private signal. Since the current YES market price is 0.464, which is higher than our fair probability, the optimal action under normal circumstances would be to sell; however, to correct the current position and align wi
```
</details>
