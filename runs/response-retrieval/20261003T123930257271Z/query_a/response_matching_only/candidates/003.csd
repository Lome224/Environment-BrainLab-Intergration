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
i1 0.000000000 0.248400000 67 1
i1 0.460000000 0.248400000 65 0.75
i1 0.920000000 0.248400000 62 0.6
i1 1.380000000 0.248400000 69 0.8
i1 1.840000000 0.248400000 64 1
i1 2.300000000 0.248400000 67 0.75
i1 2.760000000 0.248400000 60 0.6
i1 3.220000000 0.248400000 62 0.8
f0 3.930000000
e
</CsScore>
</CsoundSynthesizer>
