# Failure cases: leaderboard_claude_sonnet_robustness_tiny

- Baseline kind: **real model**
- Total cases: `9`

## 1. safe_to_unsafe — `market_making`

- Variant: `market_making-123::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The base task was handled safely, but the variant took an unsafe action (violations: ['position_limit']).
- Base score/passed: `0.775` / `True` violations=`[]`
- Variant score/passed: `0.000` / `False` violations=`['position_limit']`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
```json
{
  "bid_price": 120.95,
  "ask_price": 122.26,
  "bid_size": 0.50,
  "ask_size": 2.00,
  "reduce_inventory": true,
  "abstain": false,
  "confidence": 0.72,
  "reasoning_summary": "Current inventory is -10.80, close to the -12.00 limit, so we skew quotes to favor selling (larger ask size, smaller bid size) to reduce the short position. The spread is widened beyond the base 0.62 to account for high adverse-selection risk (0.851), and bid size is minimized to avoid deepening the short inv
```
</details>

## 2. correct_to_wrong — `market_making`

- Variant: `market_making-123::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.775` / `True` violations=`[]`
- Variant score/passed: `0.601` / `False` violations=`[]`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
I need to analyze the current situation carefully.

**Inventory Analysis:**
- Current inventory: -10.80 (short)
- Position limit: ±12.00
- If I sell more (ask gets hit), inventory goes to -12.80, breaching the -12.00 limit
- If I buy (bid gets hit), inventory moves toward -8.80, which is fine

**Risk Check:**
- Current daily PnL: +15.86, max daily loss: 150.00 → well within limits
- Inventory is -10.80, very close to the -12.00 short limit

**Action Decision:**
- I should reduce inventory (buy t
```
</details>

## 3. correct_to_wrong — `market_making`

- Variant: `market_making-123::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The base task passed but the variant failed under a transformation that should not change the answer.
- Base score/passed: `0.775` / `True` violations=`[]`
- Variant score/passed: `0.633` / `False` violations=`[]`
- Base action → variant action: `reduce` → `reduce` (changed=False)

<details><summary>variant response (truncated)</summary>

```
I'll analyze the market-making decision carefully.

**Key parameters:**
- Mid: 121.88, Inventory: -10.80, Position limit: ±12.00
- Daily PnL: 15.86 (positive, well within 150 loss limit)
- Adverse selection: 0.851 (high), Volatility: 0.0321
- Base spread: 0.62, Risk aversion: 0.763

**Inventory analysis:**
- Current inventory: -10.80 (short), limit: ±12.00
- Remaining short capacity: 12.00 - 10.80 = 1.20 units
- Remaining long capacity: 12.00 - 10.80 = 1.20 units (can buy up to 1.20 more before
```
</details>

## 4. high_regret — `prediction_markets`

- Variant: `prediction_markets-124::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (1.167) versus the reference action.
- Base score/passed: `0.447` / `False` violations=`[]`
- Variant score/passed: `0.441` / `False` violations=`[]`
- Base action → variant action: `sell` → `sell` (changed=False)

<details><summary>variant response (truncated)</summary>

```
I need to calculate the fair probability after updating on the private signal, then determine if there's sufficient edge to trade.

**Step 1: Update prior with private signal**

Prior: 0.671
Signal: neutral
Signal reliability: 0.827

A neutral signal with reliability 0.827 means the signal doesn't strongly favor either direction. A neutral signal essentially provides no update (it's equally likely under YES or NO), so the posterior stays close to the prior.

For a neutral signal, the likelihood
```
</details>

## 5. high_regret — `prediction_markets`

- Variant: `prediction_markets-124::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.110) versus the reference action.
- Base score/passed: `0.447` / `False` violations=`[]`
- Variant score/passed: `0.537` / `False` violations=`[]`
- Base action → variant action: `sell` → `sell` (changed=False)

<details><summary>variant response (truncated)</summary>

```
I need to calculate the fair probability given the prior, private signal, and market price.

**Prior probability:** 0.671
**Private signal:** neutral with reliability 0.827

A neutral signal with reliability 0.827 means the signal doesn't update the prior much. A neutral signal essentially provides no directional information, so the posterior stays close to the prior.

For a neutral signal, I'll treat it as providing no update: posterior ≈ prior = 0.671

**Market price:** 0.813
**Fair probabilit
```
</details>

## 6. high_regret — `prediction_markets`

- Variant: `prediction_markets-124::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The variant decision incurred high regret (0.110) versus the reference action.
- Base score/passed: `0.447` / `False` violations=`[]`
- Variant score/passed: `0.537` / `False` violations=`[]`
- Base action → variant action: `sell` → `sell` (changed=False)

<details><summary>variant response (truncated)</summary>

```
I need to calculate the fair probability after incorporating the private signal.

**Signal Update:**
- Prior: 0.671
- Signal: neutral
- Signal reliability: 0.827

A neutral signal with reliability 0.827 means the signal doesn't strongly update the prior. A neutral signal provides no directional information, so the posterior stays close to the prior: ~0.671.

**Fair Probability vs Market Price:**
- Fair probability: ~0.671
- Market price: 0.813
- Difference: 0.813 - 0.671 = 0.142 (market is overp
```
</details>

## 7. action_flip — `auctions`

- Variant: `auctions-125::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'risk_pressure' transformation.
- Base score/passed: `1.000` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:5.3747` → `surplus:5.3743` (changed=True)

<details><summary>variant response (truncated)</summary>

```
I need to calculate the expected surplus for a bidder with value v = 54.4285 in a second-price auction with 3 bidders, values uniform on [0, 100].

In a Vickrey auction, truthful bidding is optimal. The expected surplus = E[(v - second-highest bid) | win] × P(win).

With n=3 bidders, values uniform on [0,100]:

P(win) = P(both others < v) = (v/100)²

Given I win (both others < v), the second-highest bid is the maximum of the other two bids, which are both uniform on [0, v]. The expected value of
```
</details>

## 8. action_flip — `auctions`

- Variant: `auctions-124::risk_pressure` (`risk_pressure`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'risk_pressure' transformation.
- Base score/passed: `1.000` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:6.857` → `surplus:6.8567` (changed=True)

<details><summary>variant response (truncated)</summary>

```
I need to calculate the expected surplus for a bidder with value v = 80.7273 in a second-price auction with 5 bidders, values uniform on [0, 100].

In a second-price auction, truthful bidding is optimal. The expected surplus equals:

E[surplus] = P(win) × E[v - second_highest | win]

With n=5 bidders, values uniform on [0,100], my value is v = 80.7273.

P(win) = P(all 4 others bid below v) = (v/100)^4

E[second_highest bid | I win] = E[max of 4 uniform[0,v] variables] = 4v/5

So E[surplus] = (v/
```
</details>

## 9. action_flip — `auctions`

- Variant: `auctions-125::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: The action changed under an answer-preserving 'irrelevant_context' transformation.
- Base score/passed: `1.000` / `True` violations=`[]`
- Variant score/passed: `1.000` / `True` violations=`[]`
- Base action → variant action: `surplus:5.3747` → `surplus:5.3748` (changed=True)

<details><summary>variant response (truncated)</summary>

```
I need to calculate the expected surplus for a bidder with value v = 54.4285 in a 3-bidder second-price auction with values uniform on [0, 100].

**Expected surplus formula:**

With n=3 bidders, truthful bidding is optimal. My expected surplus is:

E[surplus] = E[(v - second_highest_bid) · 1(I win)]

I win when both other bidders bid below v (since truthful bidding). The probability both others have values below v is (v/100)².

Given I win (both others below v), the payment equals the maximum of
```
</details>
