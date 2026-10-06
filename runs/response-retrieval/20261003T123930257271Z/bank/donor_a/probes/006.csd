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
 aEnv linseg 0, 0.014500000, 1, p3-0.052500000, 1, 0.038000000, 0
 out aFiltered*aEnv
endin
</CsInstruments>
<CsScore>
i1 0.000000000 0.264000000 60 1
i1 0.400000000 0.264000000 64 0.65
i1 0.800000000 0.264000000 67 0.8
i1 1.200000000 0.264000000 69 0.65
i1 1.600000000 0.264000000 67 1
i1 2.000000000 0.264000000 64 0.65
i1 2.400000000 0.264000000 62 0.8
i1 2.800000000 0.264000000 60 0.65
f0 3.450000000
e
</CsScore>
</CsoundSynthesizer>
