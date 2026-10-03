"""Make gain-only, RMS-matched copies of the three pilot recordings."""
from pathlib import Path
import hashlib
import json
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / 'runs/lowpass-melody'
    destination = source / 'level-matched'
    if destination.exists():
        raise FileExistsError(f'Output folder already exists; preserving it: {destination}')
    clips = []
    for cutoff in (400, 1200, 6000):
        path = source / f'melody-cutoff-{cutoff}Hz.wav'
        audio, sr = sf.read(path, dtype='float64')
        if sr != 48000 or audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
            raise ValueError(f'Expected finite mono 48 kHz audio: {path}')
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms <= 0 or np.max(np.abs(audio)) >= 1:
            raise ValueError(f'Silent or clipped input: {path}')
        clips.append((cutoff, path, audio, sr, rms, hashlib.sha256(path.read_bytes()).hexdigest()))
    if len({len(clip[2]) for clip in clips}) != 1:
        raise ValueError('Input durations differ')
    # Attenuate to the quietest original; no recording needs amplification.
    target = min(clip[4] for clip in clips)
    destination.mkdir()
    records = []
    for cutoff, path, audio, sr, rms, original_hash in clips:
        gain = target / rms
        out = destination / path.name
        sf.write(out, audio * gain, sr, subtype='FLOAT')
        saved, saved_sr = sf.read(out, dtype='float64')
        measured = float(np.sqrt(np.mean(saved ** 2)))
        peak = float(np.max(np.abs(saved)))
        assert saved_sr == sr and saved.shape == audio.shape
        assert np.isfinite(saved).all() and peak < 1
        assert np.isclose(measured, target, rtol=1e-6, atol=1e-9)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == original_hash
        records.append(dict(cutoff_hz=cutoff, filename=out.name,
                            original_sha256=original_hash, original_rms=rms,
                            gain=gain, gain_db=float(20*np.log10(gain)),
                            saved_rms=measured, saved_peak=peak,
                            duration_seconds=len(saved)/sr,
                            saved_sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
        print(f'{cutoff} Hz: gain {gain:.6f}, RMS {measured:.8f}, peak {peak:.6f}; PASS')
    report = dict(method='Constant gain per complete clip; RMS includes silence',
                  target_rms=target, target_selection='Lowest input RMS; attenuation only',
                  sample_rate=48000, channels=1, output_format='32-bit float WAV',
                  limitation='Equal RMS does not guarantee equal perceived loudness',
                  originals_unchanged=True, files=records)
    (destination / 'level-matching.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Saved three audio copies and one shared report in {destination}')


if __name__ == '__main__':
    main()
