<CsoundSynthesizer>
<CsOptions>
</CsOptions>
<CsInstruments>
sr = 48000
ksmps = 32
nchnls = 1
0dbfs = 1
instr 1
aenv linseg 0, 0.03, 0.18, p3-0.13, 0.18, 0.1, 0
asig oscili aenv, p4
out asig
endin
</CsInstruments>
<CsScore>
i1 0 1 261.6256
i1 1.2 1 329.6276
i1 2.4 1 391.9954
i1 3.6 1.4 523.2511
f0 6
e
</CsScore>
</CsoundSynthesizer>
