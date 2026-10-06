## Initial listening observations

Date: 2026-10-03

- 400 Hz: muffled.
- 1200 Hz: brighter.
- 6000 Hz: brightest, sharp.

These observations were recorded before inspecting CLAP scores for this experiment.

## Analysis after viewing CLAP scores

Bright-minus-muffled similarity:
- 400 Hz: 0.1127
- 1200 Hz: 0.1029
- 6000 Hz: 0.1332

I heard brightness increase with cutoff. CLAP’s relative brightness
preference did not increase consistently: it ranked 6000 Hz highest,
then 400 Hz, then 1200 Hz.

The bright-description similarity alone decreased with cutoff.

This three-recording pilot shows partial disagreement with my
listening observations. It does not establish whether the scores
reliably measure brightness. The recordings also differ in level,
which is a possible confounding factor.

## CLAP scores after RMS level reach match
After matching the recordings’ RMS levels, CLAP’s brightness-preference ranking remained unchanged. Equalizing RMS did not restore the expected increasing order with cutoff in this pilot.

# Prompt wording test

Using the same level-matched recordings:
- Bright/dark: preference decreased as cutoff increased.
- Sharp/muffled: preference increased as cutoff increased.
- Upper harmonics: 6000 Hz ranked highest, but the lower two were reversed.

The ranking depends on the descriptions in this pilot.
These descriptions express related, but not identical, qualities.
I should not select only the pair that agrees with my expectations.

- Render the same melody at 400, 1,200, and 6,000 Hz cutoff → hear muffled → brighter → brightest.
- Record listening observations → score each audio against bright/sharp and dark/muffled descriptions.
- Calculate bright score − muffled score → scores do not increase consistently with cutoff.
- Match RMS levels → rescore with the same descriptions → disagreement remains.
- Keep audio unchanged → test three description pairs → score patterns change with the descriptions.
- Finding: CLAP’s score differences do not consistently follow the brightness change I hear.


#Summary

I heard the recordings become brighter as the filter cutoff increased from 400 Hz to 1,200 Hz to 6,000 Hz. However, CLAP’s score differences did not consistently increase in that same sequence. Matching the recordings’ RMS levels did not resolve this disagreement. When I tested different text descriptions on the same audio files, the pattern of score differences changed. The recordings themselves remained unchanged during these text comparisons.

#Question

“How should I validate or redesign the semantic objective before optimizing it?”
