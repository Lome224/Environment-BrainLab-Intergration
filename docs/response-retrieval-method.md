# Measured-response retrieval for expressive edits: prototype specification

3 October 2026 · Salome's independent research prototype · version 0.1

## What we are testing

A previous edit may work differently on another musical passage. We test whether small trial changes on the new passage help select and adapt useful edits from a bank.

The first fixture asks for more detached articulation while protecting the relative accent pattern and a coarse measure of spectral balance. This is deliberately narrow. Success here would justify a larger experiment; it would not demonstrate broad understanding of creative language or establish conference-level novelty.

The contribution under investigation is the choice and transport of executable edits using local measured responses. CLAP, finite differences, nearest-neighbor retrieval, and ridge regression are existing tools. The present combination remains a research hypothesis.

## Inputs, renderer, and controls

For a passage x and normalized controls z, the rendered audio is y = S(x,z). The score fixes pitches, onset times, event count, and written accent multipliers. Gate changes note duration, so duration is explicitly editable. The renderer is a fixed sawtooth instrument with a low-pass filter and an amplitude envelope.

The four controls, each normalized to [0,1], are:

| Coordinate | Physical mapping |
|---|---|
| Cutoff | 400 × 15^z Hz |
| Gate | 0.30 + 0.60z, multiplied by the passage's note spacing |
| Attack | 0.005 + 0.050z seconds |
| Release | 0.010 + 0.070z seconds |

The baseline is z0 = (0.55, 0.60, 0.25, 0.40). Every final edit changes at most two coordinates, each by at most 0.25. All resulting coordinates must lie in [0,1], and the envelope must fit within the edited note duration. These restrictions are checked before rendering. The implemented experiment is restricted to this baseline and bounded neighborhood; it is not an adapter for arbitrary presets.

## Semantic and preservation measurements

The fixed text pair is:

- “A synthesized melody played with short, detached, clearly separated notes.”
- “A synthesized melody played with sustained, smoothly connected notes.”

With normalized CLAP audio embedding a(y) and text embeddings t+ and t−:

\[
m(y)=a(y)^\top t_+ - a(y)^\top t_-.
\]

This margin is a proxy for relative text association, not a probability or a listener judgment. Improvement is m(y) − m(y0). Its sign cannot establish perceived detachment without independent evaluation.

For each of eight fixed score intervals, compute RMS level. Normalize the resulting eight-element vector to unit Euclidean norm, obtaining v(y). This measures relative energy across notes without requiring their absolute overall level to remain fixed. Also compute a power-weighted spectral centroid c(y) using 2,048-sample Hann windows and a 1,024-sample hop.

An edited render passes the provisional preservation checks when:

\[
|\log(c(y)/c(y_0))|\leq0.10,
\qquad \max_i |v_i(y)-v_i(y_0)|\leq0.08.
\]

These are pilot tolerances, not perceptually validated thresholds. A centroid match does not prove timbre preservation, and RMS-pattern agreement does not prove perceived accent preservation. The unprocessed render is evaluated without loudness normalization, so loudness remains a possible confound for CLAP. Record overall RMS and inspect it before interpreting semantic gains.

## Measuring the local response

Define the scaled response vector relative to each passage's own baseline:

\[
r_x(z)=\left[
\frac{m(S(x,z))-m(y_0)}{0.05},\;
\frac{\log(c(S(x,z))/c(y_0))}{0.10},\;
\frac{v(S(x,z))-v(y_0)}{0.08\sqrt{8}}
\right].
\]

It has ten components: one semantic margin, one spectral measurement, and eight accent measurements. The scales are fixed in advance; the accent vector receives a correction for its eight components.

For each control j, render z0 ± he_j with h = 0.06. The response matrix is:

\[
J_x[:,j]=\frac{r_x(z_0+he_j)-r_x(z_0-he_j)}{2h}.
\]

This costs eight probes plus one baseline render. J is a local approximation and can fail for larger or interacting edits. Every final proposal is therefore rendered and measured directly.

## Offline bank

Two fixed synthetic donor passages form the bank. Each contributes nine baseline/probe renders and twelve edit renders: positive/negative 0.20 changes to each control, plus four gate/release combinations. Total offline construction cost: 42 renders.

An entry stores the donor passage, baseline controls/audio, changed controls, edited audio, measurements, and J. The query passages are separate fixtures and never appear in bank construction. This small split checks the procedure; it cannot establish generalization to human performances, different instruments, or unfamiliar control systems.

## Retrieval and adaptation rule

For donor edit d with support A (its changed controls), ordinary retrieval scores:

\[
R_d=\frac{m(y_d^{edit})}{0.05}+a(y_q^0)^\top a(y_d^0).
\]

This combines donor target association and original-audio similarity. It is a simple baseline, not a reproduction of SynthScribe.

Response-informed retrieval subtracts the mean squared difference between the probe-scaled response matrices on the donor's changed controls:

\[
D_d=\operatorname{mean}\left([h(J_q[:,A]-J_d[:,A])]^2\right),
\qquad R_d^{response}=R_d-D_d.
\]

It then adapts the donor edit by solving:

\[
u^*=\arg\min_u\|J_q[:,A]u-r_d(z_d^0+\Delta z_d)\|_2^2
+0.1\|u-\Delta z_d[A]\|_2^2.
\]

The implementation uses the closed-form ridge solution and clips each changed coordinate to ±0.25. Clipping is a practical proposal rule; it is not the exact solution of a box-constrained least-squares problem. All other coordinates remain zero. Candidate edits use one-half and full adapted strength. Distinct admissible candidates are rendered in descending retrieval-score order, with deterministic ordering for ties.

This mechanism combines response-based selection and response-based transport. The default three-method pilot does not isolate their individual effects. The optional `--ablations` run adds matching without transport and transport without response matching; both use the same nine initial renders and remaining proposal budget.

## Equal-budget comparison

The default online budget is thirteen real renders for each method on each query. Offline bank construction is reported separately. No method gets free cached query renders, and all may select any admissible render they actually evaluated, including probes.

| Method | Budget allocation |
|---|---|
| Ordinary retrieval | One baseline + twelve retrieved/scaled donor edits |
| Response-informed retrieval | One baseline + eight probes + four adapted edits |
| Local search without retrieval | One baseline + eight probes + four locally proposed edits |

Local search enumerates one- and two-control edits with magnitudes 0.12 or 0.24. It ranks them using J's predicted semantic gain, penalizes predicted preservation violations, and applies a small change-magnitude penalty. It then renders the top four. This baseline directly tests whether local measurements alone explain an advantage.

Each method returns its highest-margin render satisfying the actual preservation checks and edit limits. The unchanged baseline remains eligible. A zero-edit result means no evaluated admissible candidate improved the proxy; it does not prove that no useful edit exists.

## Interpreting the first run

The initial run uses one held-out synthetic melody and one seed. Its purpose is to check rendering, scoring, candidate selection, constraints, bookkeeping, and reproducibility. No statistical or perceptual conclusion follows from three selected clips.

Proceed to a larger study only after inspecting the selected audio and side effects. Required comparisons include response matching without transport, transport without response matching, ordinary retrieval with comparable local refinement, a simple gate-length heuristic, and a suitable direct optimizer. Hold rendering budgets constant, report offline cost, and predefine passage splits and prompt variants. Evaluate target intent and protected qualities with listeners independently of CLAP.

The hypothesis is weakened if local search without retrieval performs equally well, if gains depend on one prompt pair, or if apparent improvements reflect loudness changes or preservation violations. A null result should change the research claim rather than prompt-selecting until the desired outcome appears.

## Relation to existing work

[SynthScribe](https://arxiv.org/html/2312.04690v2) already retrieves presets, transfers control groups, and estimates parameter relevance. [SaxEx](https://jlarcos.github.io/projects/music/Saxex.html) already retrieves expressive examples using musical context. [Audio transformation representations](https://arxiv.org/html/2608.28127v1) already study transformation retrieval across sources. The proposed distinction is using locally measured renderer responses for constrained edit selection and transport; it remains to be shown useful and sufficiently distinct.

## Running and records

From the project terminal with its existing Python environment:

```sh
python scripts/response_retrieval_pilot.py
```

For both fixed query fixtures:

```sh
python scripts/response_retrieval_pilot.py --queries query_a query_b
```

To include the two mechanism ablations on both fixtures:

```sh
python scripts/response_retrieval_pilot.py --queries query_a query_b --ablations
```

Every run creates a new timestamped directory under `runs/response-retrieval/`, preserving earlier work. It contains the script snapshot, configuration and final report, bank records, all rendered WAV/Csound pairs, a results table, and one selected WAV per method. Scoring uses cached LAION-CLAP on CPU with network access disabled. No model training, BrainLab integration, EEG, or hardware purchase is involved.
