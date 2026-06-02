# Failure cases: robustness_mock_bayes

- Baseline kind: **mock agent (diagnostic baseline)**
- Total cases: `25`

## 1. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-137::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.889` / `False` violations=`[]`
- Variant score/passed: `0.458` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.16272438721762358, 0.43271119098657856, 0.4045644217957978], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 2. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-136::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.734` / `False` violations=`[]`
- Variant score/passed: `0.411` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.28481810632238663, 0.6279372185632389, 0.05733784527435176, 0.029906829840022676], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 3. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-126::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.782` / `False` violations=`[]`
- Variant score/passed: `0.494` / `False` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.6774674113924634, 0.32253258860753664], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 4. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-138::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.907` / `False` violations=`[]`
- Variant score/passed: `0.780` / `False` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:2` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.3249824958534545, 0.29263695875007373, 0.3823805453964718], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 5. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-145::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.704` / `False` violations=`[]`
- Variant score/passed: `0.586` / `False` violations=`[]`
- Base action → variant action: `argmax:2` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.4510680814900885, 0.1849674846207155, 0.36396443388919614], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 6. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-129::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.567` / `False` violations=`[]`
- Variant score/passed: `0.455` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.13777709938121763, 0.6223427497104476, 0.2398801509083348], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 7. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-134::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.844` / `False` violations=`[]`
- Variant score/passed: `0.733` / `False` violations=`[]`
- Base action → variant action: `argmax:3` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.3814999923452872, 0.29664325717652107, 0.20015267237653375, 0.12170407810165801], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 8. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-132::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.669` / `False` violations=`[]`
- Variant score/passed: `0.669` / `False` violations=`[]`
- Base action → variant action: `argmax:3` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.1154034572582248, 0.45932493911894623, 0.33536139162983736, 0.08991021199299154], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 9. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-135::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.849` / `False` violations=`[]`
- Variant score/passed: `0.864` / `False` violations=`[]`
- Base action → variant action: `argmax:2` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.5805855081177039, 0.22711385971882433, 0.19230063216347176], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 10. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-131::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.517` / `False` violations=`[]`
- Variant score/passed: `0.552` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:2` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.18111990829947314, 0.3450449623524468, 0.47383512934808003], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 11. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-124::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.688` / `False` violations=`[]`
- Variant score/passed: `0.759` / `False` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:3` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.22872372905518487, 0.2955226538040282, 0.1497729159820338, 0.325980701158753], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 12. paraphrase_action_flip — `bayesian_games`

- Variant: `bayesian_games-139::paraphrase` (`paraphrase`, answer_preserving=True)
- Why interesting: The chosen action flipped under a meaning-preserving paraphrase.
- Base score/passed: `0.214` / `False` violations=`[]`
- Variant score/passed: `0.471` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.30187272322239905, 0.37929195486328643, 0.3188353219143144], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 13. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-123::order_permutation` (`order_permutation`, answer_preserving=True)
- Why interesting: Score dropped by 0.75 under an answer-preserving transformation.
- Base score/passed: `0.864` / `False` violations=`[]`
- Variant score/passed: `0.110` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.06801764442004622, 0.9319823555799538], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 14. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-123::misleading_authority` (`misleading_authority`, answer_preserving=True)
- Why interesting: Score dropped by 0.65 under an answer-preserving transformation.
- Base score/passed: `0.864` / `False` violations=`[]`
- Variant score/passed: `0.210` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.16876175027710125, 0.8312382497228987], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 15. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-142::misleading_authority` (`misleading_authority`, answer_preserving=True)
- Why interesting: Score dropped by 0.58 under an answer-preserving transformation.
- Base score/passed: `0.929` / `False` violations=`[]`
- Variant score/passed: `0.350` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.21968046865437377, 0.7803195313456263], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 16. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-142::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: Score dropped by 0.55 under an answer-preserving transformation.
- Base score/passed: `0.929` / `False` violations=`[]`
- Variant score/passed: `0.380` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.24979732680604533, 0.7502026731939546], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 17. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-133::order_permutation` (`order_permutation`, answer_preserving=True)
- Why interesting: Score dropped by 0.51 under an answer-preserving transformation.
- Base score/passed: `0.916` / `False` violations=`[]`
- Variant score/passed: `0.405` / `False` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.7334342960070127, 0.014269469911099173, 0.25229623408188806], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 18. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-137::misleading_authority` (`misleading_authority`, answer_preserving=True)
- Why interesting: Score dropped by 0.48 under an answer-preserving transformation.
- Base score/passed: `0.889` / `False` violations=`[]`
- Variant score/passed: `0.411` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.11610843819060207, 0.5603299899188195, 0.3235615718905784], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 19. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-144::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: Score dropped by 0.47 under an answer-preserving transformation.
- Base score/passed: `0.742` / `False` violations=`[]`
- Variant score/passed: `0.271` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.10454075011253537, 0.8954592498874646], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 20. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-123::emotional_pressure` (`emotional_pressure`, answer_preserving=True)
- Why interesting: Score dropped by 0.44 under an answer-preserving transformation.
- Base score/passed: `0.864` / `False` violations=`[]`
- Variant score/passed: `0.422` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.3800390388634686, 0.6199609611365313], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 21. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-140::emotional_pressure` (`emotional_pressure`, answer_preserving=True)
- Why interesting: Score dropped by 0.44 under an answer-preserving transformation.
- Base score/passed: `0.813` / `False` violations=`[]`
- Variant score/passed: `0.373` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:2` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.00976476454659848, 0.38025866307951023, 0.6099765723738912], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 22. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-132::irrelevant_context` (`irrelevant_context`, answer_preserving=True)
- Why interesting: Score dropped by 0.43 under an answer-preserving transformation.
- Base score/passed: `0.669` / `False` violations=`[]`
- Variant score/passed: `0.241` / `False` violations=`[]`
- Base action → variant action: `argmax:3` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.5134269663090931, 0.0026593589040562722, 0.47589369092648365, 0.008019983860366934], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 23. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-141::order_permutation` (`order_permutation`, answer_preserving=True)
- Why interesting: Score dropped by 0.41 under an answer-preserving transformation.
- Base score/passed: `0.721` / `False` violations=`[]`
- Variant score/passed: `0.314` / `False` violations=`[]`
- Base action → variant action: `argmax:1` → `argmax:0` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.7471185437283032, 0.08704785960728494, 0.1658335966644119], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 24. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-146::misleading_authority` (`misleading_authority`, answer_preserving=True)
- Why interesting: Score dropped by 0.39 under an answer-preserving transformation.
- Base score/passed: `0.732` / `False` violations=`[]`
- Variant score/passed: `0.337` / `False` violations=`[]`
- Base action → variant action: `argmax:2` → `argmax:3` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.35563043202608274, 0.17183495930601225, 0.017931442819232528, 0.4546031658486725], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

## 25. large_score_drop — `bayesian_games`

- Variant: `bayesian_games-142::order_permutation` (`order_permutation`, answer_preserving=True)
- Why interesting: Score dropped by 0.39 under an answer-preserving transformation.
- Base score/passed: `0.929` / `False` violations=`[]`
- Variant score/passed: `0.541` / `False` violations=`[]`
- Base action → variant action: `argmax:0` → `argmax:1` (changed=True)

<details><summary>variant response (truncated)</summary>

```
{"posterior": [0.41089401327187314, 0.5891059867281269], "reasoning_summary": "Deterministic random valid mock answer; not a model output."}
```
</details>

