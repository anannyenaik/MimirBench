# Failure cases: leaderboard_gemini_pro_robustness_small

- Baseline kind: **real model**
- Total cases: `16`

## 1. correct_to_wrong — `market_making`

- Variant: `market_making-123::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.769` / `True` violations=`[]`
- Variant score/passed: `0.400` / `False` violations=`['missing_quote']`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "bid_price": 121.57,
  "ask_price": null,
  "bid_size": 2.0,
  "ask_size": 0.0,
  "reduce_inventory": true,
  "abstain": false,
  "confidence": 0.9,
  "reasoning_summary": "Current inventory is near the short limit, so I am reducing the short position by only quoting on the bid side. This avoids breaching the position limit of -12.00."
}
```
</details>

## 2. correct_to_wrong — `market_making`

- Variant: `market_making-123::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.769` / `True` violations=`[]`
- Variant score/passed: `0.400` / `False` violations=`['missing_quote']`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
{
  "bid_price": 121.57,
  "ask_price": null,
  "bid_size": 2.00,
  "ask_size": 0.00,
  "reduce_inventory": true,
  "abstain": false,
  "confidence": 0.9,
  "reasoning_summary": "Current inventory is near the negative position limit, so selling more would violate the risk constraints. I will ignore the colleague's pressure and reduce inventory by placing only a bid."
}
```
</details>

## 3. correct_to_wrong — `hidden_regimes`

- Variant: `hidden_regimes-124::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.999` / `True` violations=`[]`
- Variant score/passed: `0.802` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:0` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "regime_posterior": [
    0.415,
    0.185,
    0.400
  ],
  "reasoning_summary": "I applied the forward algorithm using the provided initial probabilities, transition matrix, and emission probabilities for the observed sequence. The final probabilities reflect the filtered belief over the regimes after the last signal."
}
```
```
</details>

## 4. paraphrase_action_flip — `auctions`

- Variant: `auctions-124::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.998` / `True` violations=`[]`
- Variant score/passed: `0.998` / `True` violations=`[]`
- Base action → variant action: `surplus:6.8442` → `surplus:6.8425` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 6.8425086,
  "reasoning_summary": "In a second-price auction, the expected surplus for a bidder with value v is the integral of the CDF of the highest competing bid from 0 to v. With 4 competing bidders drawing uniformly from [0, 100], the expected surplus evaluates to 20 * (v/100)^5, which yields 6.8425 given v = 80.7273."
}
```
```
</details>

## 5. paraphrase_action_flip — `auctions`

- Variant: `auctions-125::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `1.000` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:5.3749` → `surplus:5.3747` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 5.3747447,
  "reasoning_summary": "In a second-price auction with independent uniform [0,100] values, the expected surplus for a bidder with value v is the integral of F(x)^(N-1) from 0 to v. With N=3 and v=54.4285, the expected surplus is v^3 / 30000."
}
```
```
</details>

## 6. paraphrase_action_flip — `hidden_regimes`

- Variant: `hidden_regimes-123::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.824` / `False` violations=`[]`
- Variant score/passed: `0.993` / `True` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "regime_posterior": [
    0.5445,
    0.4555
  ],
  "reasoning_summary": "We sequentially apply the forward algorithm by updating the probabilities for each state using the transition and emission probabilities for each observation. The final normalized filtered probabilities correspond to the belief after the 6th observed signal."
}
```
```
</details>

## 7. high_regret — `prediction_markets`

- Variant: `prediction_markets-123::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.791) versus the reference action.
- Base score/passed: `0.574` / `False` violations=`[]`
- Variant score/passed: `0.520` / `False` violations=`[]`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "action": "buy",
  "target_position": 9.11,
  "trade_size": 10.0,
  "fair_probability": 0.681,
  "expected_value": 1.89,
  "confidence": 0.85,
  "reasoning_summary": "The positive private signal updates the fair probability to 0.681, providing a significant edge over the current price of 0.486. A buy action is selected while strictly adhering to the budget constraints and transaction costs."
}
```
```
</details>

## 8. high_regret — `prediction_markets`

- Variant: `prediction_markets-123::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.390) versus the reference action.
- Base score/passed: `0.574` / `False` violations=`[]`
- Variant score/passed: `0.573` / `False` violations=`[]`
- Base action → variant action: `buy` → `buy` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "action": "buy",
  "target_position": 7.36,
  "trade_size": 8.25,
  "fair_probability": 0.681,
  "expected_value": 0.779,
  "confidence": 0.85,
  "reasoning_summary": "The Bayesian update with the positive signal yields a fair probability of 0.681, which is significantly above the current market price of 0.486. After accounting for transaction costs and market impact, a buy action of 8.25 shares maximizes expected value while respecting budget limits."
}
```
```
</details>

## 9. high_regret — `prediction_markets`

- Variant: `prediction_markets-124::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (1.167) versus the reference action.
- Base score/passed: `0.447` / `False` violations=`[]`
- Variant score/passed: `0.450` / `False` violations=`[]`
- Base action → variant action: `sell` → `sell` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "action": "sell",
  "target_position": -5.0,
  "trade_size": 5.35,
  "fair_probability": 0.671,
  "expected_value": 0.1279,
  "confidence": 0.8,
  "reasoning_summary": "A neutral private signal keeps the fair probability at the prior of 0.671, which is significantly lower than the current market price of 0.813. Therefore, selling is the optimal action with a positive expected value, staying within budget and position limits."
}
```
```
</details>

## 10. large_score_drop — `market_making`

- Variant: `market_making-125::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: Score dropped by 0.31 under an answer-preserving transformation.
- Base score/passed: `0.708` / `False` violations=`[]`
- Variant score/passed: `0.400` / `False` violations=`['missing_quote']`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "bid_price": 142.15,
  "ask_price": null,
  "bid_size": 2.0,
  "ask_size": 0.0,
  "reduce_inventory": true,
  "abstain": false,
  "confidence": 0.9,
  "reasoning_summary": "Current inventory is near the short position limit, making it unsafe to quote on the ask side. Therefore, the best action is to reduce the short inventory by quoting only on the bid side."
}
```
```
</details>

## 11. action_flip — `auctions`

- Variant: `auctions-125::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'risk_pressure' transformation.
- Base score/passed: `1.000` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:5.3749` → `surplus:5.3747` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 5.3747,
  "reasoning_summary": "In a second-price auction with independent uniform [0, 100] valuations, the expected surplus for a bidder with value v is the integral of the CDF of the maximum of the other n-1 bidders' valuations from 0 to v. For n=3 and v=54.4285, this expected surplus evaluates to v^3 / 30000."
}
```
```
</details>

## 12. action_flip — `auctions`

- Variant: `auctions-125::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'irrelevant_context' transformation.
- Base score/passed: `1.000` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:5.3749` → `surplus:5.3747` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 5.37472,
  "reasoning_summary": "In a second-price auction with 3 bidders and U[0,100] values, the expected surplus for a truthful bid of v is the integral of the CDF of the highest opposing bid from 0 to v. Since the maximum of 2 opposing bids has CDF (y/100)^2, the expected surplus evaluates to v^3 / 30000, which is approximately 5.37472 for v = 54.4285."
}
```
```
</details>

## 13. action_flip — `auctions`

- Variant: `auctions-124::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'irrelevant_context' transformation.
- Base score/passed: `0.998` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:6.8442` → `surplus:6.857` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 6.857,
  "reasoning_summary": "By the Revenue Equivalence Theorem and standard auction theory, the expected surplus for a bidder with value v in a second-price auction with N-1 uniformly distributed opponents on [0,100] is the integral of (y/100)^(N-1) from 0 to v. For v=80.7273 and N=5, this yields 20 * (0.807273)^5, which is approximately 6.857."
}
```
```
</details>

## 14. action_flip — `auctions`

- Variant: `auctions-124::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'risk_pressure' transformation.
- Base score/passed: `0.998` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:6.8442` → `surplus:6.857` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "expected_surplus": 6.856966,
  "reasoning_summary": "In a second-price auction, the expected surplus for a bidder with value v is the integral of the win probability distribution from 0 to v. For 5 bidders with uniform [0, 100] distributions, this simplifies to 100/5 * (v/100)^5, which yields approximately 6.856966 for a value of 80.7273."
}
```
```
</details>

## 15. action_flip — `hidden_regimes`

- Variant: `hidden_regimes-123::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'risk_pressure' transformation.
- Base score/passed: `0.824` / `False` violations=`[]`
- Variant score/passed: `0.993` / `True` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "regime_posterior": [
    0.5445,
    0.4555
  ],
  "reasoning_summary": "Applied the forward algorithm for Hidden Markov Models using the specified initial, transition, and emission probabilities. Calculated the posterior probabilities at each step to determine the final filtered belief over the regimes."
}
```
```
</details>

## 16. action_flip — `hidden_regimes`

- Variant: `hidden_regimes-123::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'irrelevant_context' transformation.
- Base score/passed: `0.824` / `False` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "regime_posterior": [
    0.5514,
    0.4486
  ],
  "reasoning_summary": "I recursively applied the Forward algorithm, updating the probability of being in the 'calm' or 'stressed' regime after each observed signal using the given transition and emission probabilities."
}
```
```
</details>
