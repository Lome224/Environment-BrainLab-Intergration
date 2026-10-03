<CsoundSynthesizer>
<CsOptions>
</CsOptions>
<CsInstruments>
sr = 48000
ksmps = 32
nchnls = 1
0dbfs = 1

; Override with --omacro:CUTOFF=400 (Hz), for example.
#ifndef CUTOFF
#define CUTOFF #1200#
#end

instr 1
    iFrequency = cpsmidinn(p4)
    iCutoff = $CUTOFF
    ; Fixed level, sawtooth phase, and gentle note edges for every render.
    aSaw vco2 0.2, iFrequency, 0, 0.5, 0
    aFiltered butterlp aSaw, iCutoff
    aEnvelope linseg 0, 0.015, 1, p3-0.075, 1, 0.06, 0
    out aFiltered * aEnvelope
endin
</CsInstruments>
<CsScore>
; p1 instrument, p2 start (seconds), p3 duration, p4 MIDI note.
; C4 E4 G4 A4 G4 E4 D4 C4; identical score at every cutoff.
i1 0.0 0.40 60
i1 0.5 0.40 64
i1 1.0 0.40 67
i1 1.5 0.40 69
i1 2.0 0.40 67
i1 2.5 0.40 64
i1 3.0 0.40 62
i1 3.5 0.90 60
f0 4.5
e
</CsScore>
</CsoundSynthesizer>
