"""Score the three cutoff recordings against fixed bright/muffled descriptions.

Run from the project terminal: python scripts/score_lowpass_melody.py
Uses cached models on CPU. Does not modify or normalize the source audio.
"""
from pathlib import Path
import argparse
import contextlib
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
import random

ROOT = Path(__file__).resolve().parents[1]
for key, folder in {
    'HF_HOME': '.cache/huggingface', 'TORCH_HOME': '.cache/torch',
    'MPLCONFIGDIR': '.cache/matplotlib', 'NUMBA_CACHE_DIR': '.cache/numba',
}.items():
    os.environ.setdefault(key, str(ROOT / folder))
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

PROMPTS = [
    'A short synthesized melody with a bright, sharp timbre.',
    'A short synthesized melody with a dark, muffled timbre.',
]
CUTOFFS = [400, 1200, 6000]


def main():
    import numpy as np
    import soundfile as sf
    import torch

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level-matched', action='store_true', help='Score the RMS-matched copies instead of the originals')
    args = parser.parse_args()
    folder = ROOT / 'runs/lowpass-melody'
    if args.level_matched:
        folder = folder / 'level-matched'
    for name in ('clap-scores.csv', 'clap-scores.json'):
        if (folder / name).exists():
            raise FileExistsError(f'Preserving existing results: {folder / name}')
    checkpoint = ROOT / 'models/music_audioset_epoch_15_esc_90.14.pt'
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    paths = [folder / f'melody-cutoff-{hz}Hz.wav' for hz in CUTOFFS]
    rows = []
    for hz, path in zip(CUTOFFS, paths):
        audio, sr = sf.read(path)
        if sr != 48000 or audio.ndim != 1 or not len(audio):
            raise ValueError(f'Expected nonempty mono 48 kHz audio: {path}')
        if not np.isfinite(audio).all() or not 0 < np.max(np.abs(audio)) < 1:
            raise ValueError(f'Invalid, silent, or clipped audio: {path}')
        rows.append(dict(cutoff_hz=hz, filename=path.name,
                         duration_seconds=len(audio)/sr,
                         rms=float(np.sqrt(np.mean(audio**2))),
                         audio_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    print('Loading cached CLAP model on CPU...', flush=True)
    # Keep verbose third-party loading messages in a log, including warnings.
    with (folder / 'clap-scoring.log').open('w') as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            import laion_clap
            model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base', device='cpu')
            model.load_ckpt(str(checkpoint))
            model.eval()
            with torch.inference_mode():
                a = np.asarray(model.get_audio_embedding_from_filelist(
                    [str(p) for p in paths], use_tensor=False))
                t = np.asarray(model.get_text_embedding(PROMPTS, use_tensor=False))
    if a.shape[0] != 3 or t.shape[0] != 2:
        raise ValueError('Unexpected embedding count')
    for embedding in (a, t):
        if not np.isfinite(embedding).all() or np.any(np.linalg.norm(embedding, axis=1) == 0):
            raise ValueError('Invalid CLAP embeddings')
    scores = (a / np.linalg.norm(a, axis=1, keepdims=True)) @ (t / np.linalg.norm(t, axis=1, keepdims=True)).T
    for row, (bright, muffled) in zip(rows, scores):
        row.update(bright_similarity=float(bright), muffled_similarity=float(muffled),
                   brightness_preference=float(bright)-float(muffled))

    csv_path = folder / 'clap-scores.csv'
    with csv_path.open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(), seed=42,
                  device='cpu', checkpoint=checkpoint.name,
                  prompts=dict(bright=PROMPTS[0], muffled=PROMPTS[1]),
                  metric='Cosine similarity; brightness_preference = bright minus muffled',
                  audio_processing=('RMS-matched copies' if args.level_matched else 'Original WAVs') + ' passed to LAION CLAP file-list preprocessing; no gain adjustment during scoring',
                  limitations='Three-clip exploratory pilot. Equal RMS does not guarantee equal perceived loudness. Scores are not probabilities.',
                  versions={p: importlib.metadata.version(p) for p in ['laion-clap', 'torch', 'transformers', 'numpy']},
                  results=rows)
    (folder / 'clap-scores.json').write_text(json.dumps(report, indent=2) + '\n')
    print('\nCutoff Hz    Bright    Muffled    Difference')
    for row in rows:
        print(f"{row['cutoff_hz']:9d}    {row['bright_similarity']:.4f}    {row['muffled_similarity']:.4f}    {row['brightness_preference']:+.4f}")
    print(f'\nSaved {csv_path}')
    print('Saved clap-scores.json and clap-scoring.log in the same folder.')


if __name__ == '__main__':
    main()
