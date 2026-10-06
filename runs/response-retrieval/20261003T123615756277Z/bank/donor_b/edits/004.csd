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
 aEnv linseg 0, 0.027500000, 1, p3-0.065500000, 1, 0.038000000, 0
 out aFiltered*aEnv
endin
</CsInstruments>
<CsScore>
i1 0.000000000 0.343200000 55 1
i1 0.520000000 0.343200000 62 0.7
i1 1.040000000 0.343200000 59 0.7
i1 1.560000000 0.343200000 65 0.85
i1 2.080000000 0.343200000 62 1
i1 2.600000000 0.343200000 57 0.7
i1 3.120000000 0.343200000 59 0.7
i1 3.640000000 0.343200000 55 0.85
f0 4.410000000
e
</CsScore>
</CsoundSynthesizer>
