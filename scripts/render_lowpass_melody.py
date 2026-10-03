"""Render one fixed Csound sawtooth melody at several low-pass cutoffs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/lowpass-melody.csd"
SAMPLE_RATE = 48000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoffs", nargs="+", type=float, default=[400, 1200, 6000],
                        help="Cutoff frequencies in Hz (default: 400 1200 6000)")
    parser.add_argument("--output", type=Path, default=ROOT / "runs/lowpass-melody")
    args = parser.parse_args()
    if any(not np.isfinite(c) or not 0 < c < SAMPLE_RATE / 2 for c in args.cutoffs):
        parser.error("Every cutoff must be finite, positive, and below 24000 Hz.")
    if len(set(args.cutoffs)) != len(args.cutoffs):
        parser.error("Choose distinct cutoffs.")

    binary = shutil.which("csound") or "/usr/local/bin/csound"
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    csd = out / SOURCE.name
    csd.write_bytes(SOURCE.read_bytes())
    clips, records = [], []
    for cutoff in args.cutoffs:
        cutoff_label = format(cutoff, ".17g")
        stem = f"melody-cutoff-{cutoff_label}Hz"
        wav = out / f"{stem}.wav"
        command = [binary, "-d", "-m0", "-W", "-s", f"--omacro:CUTOFF={cutoff_label}",
                   "-o", str(wav), str(csd)]
        rendered = subprocess.run(command, capture_output=True, text=True)
        (out / f"{stem}.log").write_text(rendered.stdout + rendered.stderr)
        rendered.check_returncode()
        audio, sample_rate = sf.read(wav, dtype="float64")
        peak = float(np.max(np.abs(audio)))
        if (sample_rate != SAMPLE_RATE or audio.ndim != 1
                or len(audio) != int(4.5 * SAMPLE_RATE)
                or not np.isfinite(audio).all() or not 0 < peak < 1):
            raise RuntimeError(f"Invalid or clipped audio: {wav}")
        # Sum windowed power spectra; the ratio checks how much upper-frequency
        # energy survives the filter, independently of overall signal level.
        frames = np.lib.stride_tricks.sliding_window_view(audio, 4096)[::2048]
        spectrum = np.abs(np.fft.rfft(frames * np.hanning(4096), axis=1)) ** 2
        power = spectrum.sum(axis=0)
        frequencies = np.fft.rfftfreq(4096, 1 / sample_rate)
        upper_fraction = float(power[frequencies >= 2000].sum() / power.sum())
        records.append({
            "cutoff_hz": cutoff, "wav": wav.name, "duration_seconds": len(audio) / sample_rate,
            "peak": peak, "rms": float(np.sqrt(np.mean(audio ** 2))),
            "power_fraction_above_2000_hz": upper_fraction,
            "sha256": hashlib.sha256(wav.read_bytes()).hexdigest(), "command": command,
        })
        clips.append(audio)
        print(f"Rendered {wav.name}: {len(audio)/sample_rate:.1f}s, "
              f"power above 2 kHz = {100 * upper_fraction:.3f}%", flush=True)

    gap = np.zeros(int(0.5 * SAMPLE_RATE))
    comparison_parts, segments, cursor = [], [], 0.0
    for index, (audio, record) in enumerate(zip(clips, records)):
        if index:
            comparison_parts.append(gap)
            cursor += len(gap) / SAMPLE_RATE
        segments.append({"cutoff_hz": record["cutoff_hz"], "start_seconds": cursor,
                         "end_seconds": cursor + len(audio) / SAMPLE_RATE})
        comparison_parts.append(audio)
        cursor += len(audio) / SAMPLE_RATE
    sf.write(out / "comparison.wav", np.concatenate(comparison_parts), SAMPLE_RATE,
             subtype="PCM_16")
    report = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(csd.read_bytes()).hexdigest(),
        "sample_rate": SAMPLE_RATE, "channels": 1, "format": "16-bit PCM WAV",
        "melody": "C4 E4 G4 A4 G4 E4 D4 C4",
        "oscillator": "vco2 sawtooth", "filter": "butterlp, second-order low-pass",
        "oscillator_amplitude": 0.2, "gain_normalization": False,
        "renders": records, "comparison": {"wav": "comparison.wav", "segments": segments},
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {out / 'comparison.wav'} and {out / 'report.json'}", flush=True)


if __name__ == "__main__":
    main()
