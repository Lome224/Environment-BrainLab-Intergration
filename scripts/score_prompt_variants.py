"""Test the three preselected wording pairs on the RMS-matched pilot audio."""
from score_lowpass_melody import ROOT, CUTOFFS
import contextlib
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import random

PAIRS = [
    ('bright-dark', 'A synthesized melody with a bright timbre.',
     'A synthesized melody with a dark timbre.'),
    ('sharp-muffled', 'A synthesized melody with a sharp tone.',
     'A synthesized melody with a muffled tone.'),
    ('upper-harmonics', 'A synthesized melody with prominent upper harmonics.',
     'A synthesized melody with subdued upper harmonics.'),
]


def main():
    import numpy as np
    import soundfile as sf
    import torch
    source = ROOT / 'runs/lowpass-melody/level-matched'
    previous = json.loads((source / 'clap-scores.json').read_text())
    paths = [source / f'melody-cutoff-{hz}Hz.wav' for hz in CUTOFFS]
    hashes = {}
    for cutoff, path in zip(CUTOFFS, paths):
        audio, sr = sf.read(path)
        if sr != 48000 or audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
            raise ValueError(f'Invalid input: {path}')
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        old = next(row for row in previous['results'] if row['cutoff_hz'] == cutoff)
        if hashes[path.name] != old['audio_sha256']:
            raise ValueError(f'Audio changed since the level-matched run: {path}')
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(4)
    checkpoint = ROOT / 'models/music_audioset_epoch_15_esc_90.14.pt'
    prompts = [prompt for _, positive, negative in PAIRS for prompt in (positive, negative)]
    # Include the original pair as a consistency check, not as a new candidate.
    prompts += [previous['prompts']['bright'], previous['prompts']['muffled']]
    print('Scoring fixed prompt pairs on CPU using cached models...', flush=True)
    capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            import laion_clap
            model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base', device='cpu')
            model.load_ckpt(str(checkpoint))
            model.eval()
            with torch.inference_mode():
                a = np.asarray(model.get_audio_embedding_from_filelist([str(p) for p in paths], use_tensor=False))
                t = np.asarray(model.get_text_embedding(prompts, use_tensor=False))
    except Exception:
        print(capture.getvalue())
        raise
    for embedding in (a, t):
        if not np.isfinite(embedding).all() or np.any(np.linalg.norm(embedding, axis=1) == 0):
            raise ValueError('Invalid embeddings')
    scores = (a / np.linalg.norm(a, axis=1, keepdims=True)) @ (t / np.linalg.norm(t, axis=1, keepdims=True)).T
    old_scores = np.array([[next(r for r in previous['results'] if r['cutoff_hz'] == hz)[key]
                            for key in ('bright_similarity', 'muffled_similarity')] for hz in CUTOFFS])
    if not np.allclose(scores[:, -2:], old_scores, atol=1e-5, rtol=0):
        raise ValueError('Original-prompt consistency check failed')
    rows, rankings = [], {}
    for j, (name, positive, negative) in enumerate(PAIRS):
        differences = scores[:, 2*j] - scores[:, 2*j+1]
        rankings[name] = [CUTOFFS[i] for i in np.argsort(differences)]
        for i, hz in enumerate(CUTOFFS):
            rows.append(dict(pair=name, cutoff_hz=hz, positive_prompt=positive, negative_prompt=negative,
                             positive_similarity=float(scores[i, 2*j]), negative_similarity=float(scores[i, 2*j+1]),
                             difference=float(differences[i])))
        print(name, [round(float(d), 6) for d in differences], 'ascending cutoff ranking:', rankings[name])
    destination = source / ('prompt-variants-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    destination.mkdir()
    with (destination / 'scores.csv').open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(), seed=42, device='cpu',
                  checkpoint=checkpoint.name, input_sha256=hashes,
                  versions={p: importlib.metadata.version(p) for p in ['laion-clap', 'torch', 'transformers', 'numpy']},
                  original_prompt_check_max_absolute_error=float(np.max(abs(scores[:, -2:]-old_scores))),
                  metric='Positive-description cosine similarity minus negative-description cosine similarity',
                  limitations='Exploratory wording sensitivity on three clips; pairs express related but distinct concepts; no significance test.',
                  ascending_rankings=rankings, results=rows)
    (destination / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Saved:', destination)


if __name__ == '__main__':
    main()
