"""Verify installation; the synthetic audio is not a BrainLab experiment."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
for key, directory in {
    "HF_HOME": ".cache/huggingface", "TORCH_HOME": ".cache/torch",
    "MPLCONFIGDIR": ".cache/matplotlib", "NUMBA_CACHE_DIR": ".cache/numba",
}.items():
    os.environ.setdefault(key, str(ROOT / directory))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
for scheme, proxy in urllib.request.getproxies().items():
    if scheme in ("http", "https"):
        os.environ.setdefault(f"{scheme.upper()}_PROXY", proxy)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clap", action="store_true", help="Also verify actual CLAP inference")
    args = parser.parse_args()
    import cma
    import numpy as np
    import soundfile as sf
    import torch

    started = time.time()
    out = ROOT / "runs/environment-check"
    out.mkdir(parents=True, exist_ok=True)
    binary = shutil.which("csound") or "/usr/local/bin/csound"
    csd = out / "demo.csd"
    wav = out / "demo.wav"
    csd.write_text('''<CsoundSynthesizer>
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
''')
    rendered = subprocess.run([binary, "-d", "-m0", "-W", "-o", str(wav), str(csd)], capture_output=True, text=True, check=True)
    (out / "csound.log").write_text(rendered.stdout + rendered.stderr)
    audio, sample_rate = sf.read(wav, dtype="float32")
    assert sample_rate == 48000 and len(audio) >= 48000
    assert np.isfinite(audio).all() and 0 < float(np.max(np.abs(audio))) < 1
    print(f"PASS Csound render and WAV reading: {len(audio)/sample_rate:.2f} seconds", flush=True)

    optimizer = cma.CMAEvolutionStrategy([1.5, -1.0], 0.5, {"seed": 42, "maxfevals": 600, "verbose": -9, "bounds": [-3, 3], "verb_log": 0})
    while not optimizer.stop():
        candidates = optimizer.ask()
        optimizer.tell(candidates, [float(np.dot(x, x)) for x in candidates])
    assert optimizer.result.fbest < 1e-5, optimizer.result.fbest
    print(f"PASS CMA-ES mathematical check: best loss {optimizer.result.fbest:.3g}", flush=True)

    versions = {name: importlib.metadata.version(name) for name in ["numpy", "torch", "torchaudio", "torchvision", "transformers", "laion-clap", "cma", "soundfile", "librosa"]}
    report = {"purpose": "Installation verification, not a research result", "python": sys.version, "executable": sys.executable, "platform": platform.platform(), "versions": versions, "csound_executable": binary, "sample_rate": sample_rate, "audio_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(), "cma_best_loss": float(optimizer.result.fbest), "cma_evaluations": int(optimizer.result.evaluations), "mps_available": torch.backends.mps.is_available(), "clap_tested": False}

    if args.clap:
        import laion_clap
        checkpoint = ROOT / "models/music_audioset_epoch_15_esc_90.14.pt"
        if not checkpoint.exists():
            raise FileNotFoundError(f"Download the documented official checkpoint first: {checkpoint}")
        torch.set_num_threads(min(4, os.cpu_count() or 1))
        print("Loading music CLAP checkpoint on CPU...", flush=True)
        model = laion_clap.CLAP_Module(enable_fusion=False, amodel="HTSAT-base", device="cpu")
        model.load_ckpt(str(checkpoint))
        model.eval()
        prompts = ["A short sequence of electronic musical tones.", "A dog barking outdoors."]
        with torch.inference_mode():
            audio_embedding = model.get_audio_embedding_from_filelist([str(wav)], use_tensor=False)
            text_embeddings = model.get_text_embedding(prompts, use_tensor=False)
        a = np.asarray(audio_embedding)
        t = np.asarray(text_embeddings)
        scores = (a / np.linalg.norm(a, axis=1, keepdims=True)) @ (t / np.linalg.norm(t, axis=1, keepdims=True)).T
        assert np.isfinite(scores).all()
        report.update({"clap_tested": True, "clap_device": "cpu", "clap_checkpoint": checkpoint.name, "clap_scores": dict(zip(prompts, scores[0].tolist())), "audio_embedding_shape": list(a.shape), "text_embedding_shape": list(t.shape)})
        print("PASS CLAP: finite audio and text embeddings and cosine scores", flush=True)
        print(json.dumps(report["clap_scores"], indent=2), flush=True)
    report["elapsed_seconds"] = round(time.time() - started, 2)
    name = "report-clap.json" if args.clap else "report.json"
    (out / name).write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {out / name}", flush=True)


if __name__ == "__main__":
    main()
