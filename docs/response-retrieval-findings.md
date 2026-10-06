# First prototype findings

3 October 2026

## What was completed

An exact algorithm was specified in [the method document](response-retrieval-method.md), implemented in the existing Python/Csound environment, and run with the cached LAION-CLAP model. No model training was needed. The prototype compares ordinary retrieval, response-informed retrieval, and local search without retrieval. Two additional variants test response matching without adaptation and adaptation without response matching.

**Finding: this implementation has not demonstrated a useful advantage for response-informed retrieval.** It achieved a smaller CLAP-margin improvement than the best baseline on both query passages. Removing response matching produced exactly the same candidate proposals on both passages. This is evidence against claiming a benefit for the current response-matching rule on this fixture, rather than evidence of a novel successful algorithm.

## What the numbers mean

CLAP compares each recording with two fixed descriptions: detached notes and connected notes. The detached-description similarity minus the connected-description similarity is the margin. The table shows the edited margin minus the original margin. Higher numbers mean that CLAP's relative association moved further toward the detached description. They do not establish that a listener hears greater detachment or that the edited sound is better.

| Method | Passage A: margin improvement | Passage B: margin improvement |
|---|---:|---:|
| Ordinary retrieval | +0.02349 | +0.01375 |
| Proposed response-informed retrieval | +0.02215 | +0.00269 |
| Local search without retrieval | +0.03087 | +0.00771 |
| Response matching only | +0.02322 | +0.00631 |
| Adaptation only, without response matching | +0.02215 | +0.00269 |

Local search had the largest proxy improvement on passage A. Ordinary retrieval had the largest on passage B. The proposed method did not lead on either passage.

Every method received thirteen actual renders per query. The offline bank cost forty-two additional renders. The expanded run therefore used 42 + 5 × 2 × 13 = **172 renders**. The earlier three-method, one-query smoke run used 81 renders, retained in its own folder. Query A's three original method summaries reproduced exactly in the expanded run.

All returned edits passed the two configured checks: spectral-centroid drift and relative note-energy drift. Passing these numerical checks does not establish complete timbre or accent preservation. Changed-control counts were at most two; the proposed method selected a one-control probe on passage B, so its winning output there did not come from an adapted bank edit.

## Why this does not yet establish musical success

- Only two synthetic query passages and two donor passages were used, on one instrument and one seed. They use the same baseline controls and regular note spacing.
- The semantic objective was assessed with the same CLAP model used for selection. There was no independent listener evaluation.
- The winning ordinary-retrieval edit for passage B increased gate from 0.66 to 0.78. Longer note duration is not straightforward evidence of greater detachment, even though CLAP's margin improved. This is a concrete reason to validate the semantic objective before interpreting its score as expression.
- Overall RMS changed. The proposed method's passage-A output had approximately 0.839 times the baseline RMS; the winning ordinary-retrieval passage-B output had approximately 1.108 times the baseline RMS. Loudness may influence the model or listening judgments.
- Identical global envelopes and fixed accent multipliers make accent preservation relatively easy in this fixture. More varied note lengths and phrase shapes are needed before claiming robust preservation.
- The response-matching term did not alter the actual proposals compared with adaptation alone. It is implemented and a constructed unit test shows that it can change retrieval selection, but it was ineffective on these donor/query fixtures with the fixed coefficient.
- The bank is small and the local linear model is only approximate. Failure here does not prove that every possible response-based retrieval method will fail.

The correct research statement is: **“We implemented and tested a response-informed retrieval mechanism; this small pilot did not demonstrate an advantage over simpler alternatives.”** It would be inaccurate to describe this result as confirmation of algorithmic novelty or ICMC readiness.

## Verification

Five automated tests passed: invalid-control rejection; preservation-aware output selection; pitch/onset/accent score invariants; local candidate bounds and sparsity; and a constructed example where response matching changes which donor edit is chosen.

An independent output audit checked all 172 render records against their WAV hashes, verified thirteen renders per method/query, verified the selected preservation flags, and checked the saved script hash. It also confirmed repeat-run agreement for the three original query-A summaries and identical proposals when response matching was removed.

## Files and listening

The expanded results are in [the timestamped run](../runs/response-retrieval/20261003T123930257271Z/). The [results table](../runs/response-retrieval/20261003T123930257271Z/summary.csv) and [complete report](../runs/response-retrieval/20261003T123930257271Z/report.json) retain the measured outcomes.

Listen to each passage's original and the two contrasting outputs:

| Passage | Original | Proposed method | Best CLAP-proxy baseline |
|---|---|---|---|
| A | [Original A](../runs/response-retrieval/20261003T123930257271Z/query_a/ordinary_retrieval/initial/000.wav) | [Proposed A](../runs/response-retrieval/20261003T123930257271Z/query_a/response_retrieval/selected.wav) | [Local search A](../runs/response-retrieval/20261003T123930257271Z/query_a/local_without_retrieval/selected.wav) |
| B | [Original B](../runs/response-retrieval/20261003T123930257271Z/query_b/ordinary_retrieval/initial/000.wav) | [Proposed B](../runs/response-retrieval/20261003T123930257271Z/query_b/response_retrieval/selected.wav) | [Ordinary retrieval B](../runs/response-retrieval/20261003T123930257271Z/query_b/ordinary_retrieval/selected.wav) |

These files preserve the raw rendering levels. A later controlled listening study should address loudness and conceal method identities. Personal observations at this stage can diagnose obvious problems but are not a substitute for that study.

## Next decision

Before scaling the bank or expanding BrainLab integration, check whether listeners recognize the intended articulation change in this fixture and whether the chosen semantic score follows that judgment. Then test more varied passages and a simple gate-length rule alongside the existing baselines. Any revision to matching weights or descriptors should be developed on separate development passages and assessed on newly held-out passages, rather than tuned to reverse these two results.

The current deliverable is a reproducible mechanism prototype and a documented negative pilot finding. It is useful material for an algorithm discussion with a professor: the question, implementation, competing explanations, measured results, and limitations are all explicit.
