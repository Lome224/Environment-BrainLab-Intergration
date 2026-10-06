<CsoundSynthesizer>
<CsOptions>
</CsOptions>
<CsInstruments>
sr = 48000
ksmps = 32
nchnls = 1
0dbfs = 1
instr 1
 aSaw vco2 0.15*p5, cpsmidinn(p4), 0, 0.5, 0
 aFiltered butterlp aSaw, 1773.822599725
 aEnv linseg 0, 0.017500000, 1, p3-0.055500000, 1, 0.038000000, 0
 out aFiltered*aEnv
endin
</CsInstruments>
<CsScore>
i1 0.000000000 0.361920000 48 1
i1 0.580000000 0.361920000 55 0.6
i1 1.160000000 0.361920000 52 0.85
i1 1.740000000 0.361920000 57 0.7
i1 2.320000000 0.361920000 53 1
i1 2.900000000 0.361920000 50 0.6
i1 3.480000000 0.361920000 55 0.85
i1 4.060000000 0.361920000 48 0.7
f0 4.890000000
e
</CsScore>
</CsoundSynthesizer>
