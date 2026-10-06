"""Exploratory, budget-matched Csound edit-retrieval comparison (offline CPU).

This is a mechanism prototype, not a validated semantic controller.
Run: python scripts/response_retrieval_pilot.py
"""
from __future__ import annotations

import argparse
import contextlib
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
for key, folder in {
    'HF_HOME': '.cache/huggingface', 'TORCH_HOME': '.cache/torch',
    'MPLCONFIGDIR': '.cache/matplotlib', 'NUMBA_CACHE_DIR': '.cache/numba',
}.items():
    os.environ.setdefault(key, str(ROOT / folder))
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

import numpy as np
import soundfile as sf

SR = 48000
NAMES = ['cutoff', 'gate', 'attack', 'release']
BASE = np.array([.55, .6, .25, .4])
H = .06
MAX_EDIT = .25
PROMPTS = [
    'A synthesized melody played with short, detached, clearly separated notes.',
    'A synthesized melody played with sustained, smoothly connected notes.',
]
# Synthetic fixture split is fixed before scoring. No query passage enters the bank.
PASSAGES = {
    'donor_a': dict(notes=[60, 64, 67, 69, 67, 64, 62, 60], step=.40,
                    accents=[1, .65, .8, .65, 1, .65, .8, .65]),
    'donor_b': dict(notes=[55, 62, 59, 65, 62, 57, 59, 55], step=.52,
                    accents=[1, .7, .7, .85, 1, .7, .7, .85]),
    'query_a': dict(notes=[67, 65, 62, 69, 64, 67, 60, 62], step=.46,
                    accents=[1, .75, .6, .8, 1, .75, .6, .8]),
    'query_b': dict(notes=[48, 55, 52, 57, 53, 50, 55, 48], step=.58,
                    accents=[1, .6, .85, .7, 1, .6, .85, .7]),
}


def parameters(z):
    z = np.asarray(z, dtype=float)
    if z.shape != (4,) or not np.isfinite(z).all() or np.any((z < 0) | (z > 1)):
        raise ValueError('Expected four finite normalized controls in [0,1]')
    return dict(cutoff_hz=float(400 * 15 ** z[0]), gate=float(.30 + .60*z[1]),
                attack_seconds=float(.005 + .05*z[2]),
                release_seconds=float(.01 + .07*z[3]))


def csd_text(passage, z):
    p = parameters(z)
    duration = p['gate'] * passage['step']
    # Check physical validity as well as normalized control bounds.
    if duration <= p['attack_seconds'] + p['release_seconds']:
        raise ValueError('Envelope segments exceed note duration')
    score = '\n'.join(f'i1 {i*passage["step"]:.9f} {duration:.9f} {note} {accent}'
                      for i, (note, accent) in enumerate(zip(passage['notes'], passage['accents'])))
    return f'''<CsoundSynthesizer>
<CsOptions>
</CsOptions>
<CsInstruments>
sr = {SR}
ksmps = 32
nchnls = 1
0dbfs = 1
instr 1
 aSaw vco2 0.15*p5, cpsmidinn(p4), 0, 0.5, 0
 aFiltered butterlp aSaw, {p['cutoff_hz']:.9f}
 aEnv linseg 0, {p['attack_seconds']:.9f}, 1, p3-{p['attack_seconds']+p['release_seconds']:.9f}, 1, {p['release_seconds']:.9f}, 0
 out aFiltered*aEnv
endin
</CsInstruments>
<CsScore>
{score}
f0 {len(passage['notes'])*passage['step']+.25:.9f}
e
</CsScore>
</CsoundSynthesizer>
'''


def descriptors(audio, passage):
    if not np.isfinite(audio).all() or not 0 < np.max(np.abs(audio)) < .999:
        raise ValueError('Silent, invalid or clipped render')
    frames = np.lib.stride_tricks.sliding_window_view(audio, 2048)[::1024]
    power = (np.abs(np.fft.rfft(frames * np.hanning(2048), axis=1))**2).sum(axis=0)
    centroid = float(power @ np.fft.rfftfreq(2048, 1/SR) / power.sum())
    levels = np.array([np.sqrt(np.mean(audio[round(i*passage['step']*SR):
                                                 round((i+1)*passage['step']*SR)]**2))
                       for i in range(8)])
    return centroid, levels / np.linalg.norm(levels), float(np.sqrt(np.mean(audio**2)))


class Engine:
    def __init__(self, out, seed):
        import torch
        import laion_clap
        checkpoint = ROOT / 'models/music_audioset_epoch_15_esc_90.14.pt'
        if not checkpoint.is_file():
            raise FileNotFoundError(checkpoint)
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.set_num_threads(min(4, os.cpu_count() or 1))
        self.torch, self.seed, self.out = torch, seed, out
        self.binary = shutil.which('csound') or '/usr/local/bin/csound'
        self.count = 0
        with (out/'model-load.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            self.model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base', device='cpu')
            self.model.load_ckpt(str(checkpoint))
            self.model.eval()
            with torch.inference_mode():
                t = np.asarray(self.model.get_text_embedding(PROMPTS, use_tensor=False))
        self.text = t / np.linalg.norm(t, axis=1, keepdims=True)

    def evaluate(self, passage_id, controls, folder):
        folder.mkdir(parents=True, exist_ok=False)
        paths, records = [], []
        for i, z in enumerate(controls):
            z = np.asarray(z, dtype=float)
            source = folder / f'{i:03d}.csd'
            wav = folder / f'{i:03d}.wav'
            source.write_text(csd_text(PASSAGES[passage_id], z))
            result = subprocess.run([self.binary, '-d', '-m0', '-W', '-f', '-o', str(wav), str(source)],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode:
                (folder/'render-error.log').write_text(result.stdout+result.stderr)
                result.check_returncode()
            audio, sr = sf.read(wav)
            if sr != SR or audio.ndim != 1:
                raise ValueError('Expected mono 48 kHz audio')
            centroid, accents, rms = descriptors(audio, PASSAGES[passage_id])
            paths.append(str(wav))
            records.append(dict(z=z.tolist(), physical=parameters(z), wav=str(wav.relative_to(self.out)),
                                centroid=centroid, accents=accents.tolist(), rms=rms,
                                sha256=hashlib.sha256(wav.read_bytes()).hexdigest()))
            self.count += 1
        # Each clip uses the same seed, making repeated evaluation independent of ordering.
        for path, record in zip(paths, records):
            random.seed(self.seed)
            np.random.seed(self.seed)
            self.torch.manual_seed(self.seed)
            with self.torch.inference_mode():
                a = np.asarray(self.model.get_audio_embedding_from_filelist([path], use_tensor=False))[0]
            if not np.isfinite(a).all() or np.linalg.norm(a) == 0:
                raise ValueError('Invalid embedding')
            a = a / np.linalg.norm(a)
            scores = a @ self.text.T
            record.update(embedding=a.tolist(), scores=scores.tolist(), margin=float(scores[0]-scores[1]))
        (folder/'records.json').write_text(json.dumps(records, indent=2)+'\n')
        return records


def response(record, base):
    # Fixed pilot scales, not fitted to query results. Eight accents receive total weight one.
    return np.r_[(record['margin']-base['margin'])/.05,
                 np.log(record['centroid']/base['centroid'])/.10,
                 (np.array(record['accents'])-base['accents'])/(.08*np.sqrt(8))]


def jacobian(records):
    base = records[0]
    return np.stack([(response(records[1+2*j], base)-response(records[2+2*j], base))/(2*H)
                     for j in range(4)], axis=1)


def probe_controls():
    return [BASE.copy()] + [BASE + sign*H*np.eye(4)[j] for j in range(4) for sign in (1, -1)]


def allowed(delta):
    delta = np.asarray(delta)
    return (np.isfinite(delta).all() and np.count_nonzero(np.abs(delta)>1e-8)<=2
            and np.max(np.abs(delta))<=MAX_EDIT+1e-9
            and np.all((BASE+delta >= 0) & (BASE+delta <= 1)))


def feasibility(record, base):
    centroid_drift = abs(float(np.log(record['centroid']/base['centroid'])))
    accent_drift = float(np.max(np.abs(np.array(record['accents'])-base['accents'])))
    return centroid_drift <= .10 and accent_drift <= .08, centroid_drift, accent_drift


def unique_sorted(candidates, count):
    selected, seen = [], set()
    for score, delta in sorted(candidates, key=lambda x: -x[0]):
        key = tuple(np.round(delta, 8))
        if key not in seen and allowed(delta) and np.linalg.norm(delta)>1e-8:
            selected.append(np.asarray(delta))
            seen.add(key)
        if len(selected) == count:
            return selected
    raise RuntimeError(f'Only {len(selected)} distinct admissible proposals; need {count}')


def retrieve(bank, query_base, jq, count, use_response, transport=None):
    if transport is None:
        transport = use_response
    proposals = []
    aq = np.array(query_base['embedding'])
    for entry in bank:
        delta = np.array(entry['delta'])
        support = np.flatnonzero(np.abs(delta)>1e-8)
        # Ordinary retrieval combines donor target fit and original-audio similarity.
        relevance = entry['edited']['margin']/.05 + float(aq @ entry['base']['embedding'])
        if use_response:
            jd = np.asarray(entry['jacobian'])
            # Compare local slopes only on the control families used by this donor edit.
            distance = float(np.mean((H*(jq[:, support]-jd[:, support]))**2))
            relevance -= distance
        if transport:
            # Ridge-regularized transport: target the donor's measured feature change.
            a = jq[:, support]
            rhs = response(entry['edited'], entry['base'])
            transported = np.linalg.solve(a.T@a+.1*np.eye(len(support)),
                                          a.T@rhs+.1*delta[support])
            delta = np.zeros(4)
            delta[support] = np.clip(transported, -MAX_EDIT, MAX_EDIT)
        for factor in (.5, 1.0):
            proposals.append((relevance, factor*delta))
    return unique_sorted(proposals, count)


def local_search(jq, count):
    proposals = []
    for size in (1, 2):
        for support in itertools.combinations(range(4), size):
            for values in itertools.product((-.24, -.12, .12, .24), repeat=size):
                delta = np.zeros(4)
                delta[list(support)] = values
                prediction = jq@delta
                # Soft prediction penalties guide proposals; real renders face hard checks.
                penalty = max(0., abs(prediction[1])-1.)
                penalty += max(0., np.max(np.abs(prediction[2:]))*np.sqrt(8)-1.)
                proposals.append((float(prediction[0]-2*penalty-.05*np.sum(np.abs(delta))), delta))
    return unique_sorted(proposals, count)


def select_result(records):
    base = records[0]
    feasible = [r for r in records if allowed(np.array(r['z'])-BASE) and feasibility(r, base)[0]]
    # The unchanged baseline is always eligible; do not force a failed semantic edit.
    return max(feasible, key=lambda r: (r['margin'], -np.sum(np.abs(np.array(r['z'])-BASE))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--queries', nargs='+', choices=['query_a', 'query_b'], default=['query_a'])
    parser.add_argument('--budget', type=int, default=13)
    parser.add_argument('--ablations', action='store_true', help='Also isolate response matching and transport')
    args = parser.parse_args()
    if not 10 <= args.budget <= 17:
        parser.error('Pilot budget must be between 10 and 17 renders per method/query')
    if len(set(args.queries)) != len(args.queries):
        parser.error('Query identifiers must be unique')
    out = ROOT/'runs/response-retrieval'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, out/'script-snapshot.py')
    methods = ['ordinary_retrieval', 'response_retrieval', 'local_without_retrieval']
    if args.ablations:
        methods += ['response_matching_only', 'response_transport_only']
    config = dict(seed=args.seed, queries=args.queries, budget=args.budget, methods=methods, prompts=PROMPTS,
                  baseline=BASE.tolist(), probe_step=H, max_edit=MAX_EDIT,
                  controls=NAMES, passages=PASSAGES, centroid_log_tolerance=.10,
                  accent_max_tolerance=.08, semantic_scale=.05, ridge=.1,
                  status='running', limitations='Synthetic single-instrument mechanism pilot; CLAP proxy only; no human validation.')
    (out/'report.json').write_text(json.dumps(config, indent=2)+'\n')
    print(f'Output: {out}', flush=True)
    print('Loading cached CLAP on CPU...', flush=True)
    engine = Engine(out, args.seed)
    bank = []
    # Same deterministic donor edits for every run: +/- one family, plus four pairs.
    deltas = [sign*.20*np.eye(4)[j] for j in range(4) for sign in (1, -1)]
    deltas += [np.array([0, gate, 0, release]) for gate in (-.2, .2) for release in (-.2, .2)]
    for donor in ('donor_a', 'donor_b'):
        print(f'Building {donor}: 9 baseline/probe renders + 12 edit renders', flush=True)
        probes = engine.evaluate(donor, probe_controls(), out/'bank'/donor/'probes')
        jd = jacobian(probes)
        edits = engine.evaluate(donor, [BASE+d for d in deltas], out/'bank'/donor/'edits')
        for d, edited in zip(deltas, edits):
            bank.append(dict(donor=donor, delta=d.tolist(), base=probes[0], edited=edited,
                             jacobian=jd.tolist()))
    (out/'bank.json').write_text(json.dumps(bank, indent=2)+'\n')
    offline_count = engine.count
    rows = []
    for query in args.queries:
        for method in methods:
            print(f'{query}: {method}, budget {args.budget}', flush=True)
            folder = out/query/method
            start_count = engine.count
            probing = method != 'ordinary_retrieval'
            initial = engine.evaluate(query, probe_controls() if probing else [BASE], folder/'initial')
            jq = jacobian(initial) if probing else None
            remaining = args.budget-len(initial)
            if method == 'local_without_retrieval':
                proposals = local_search(jq, remaining)
            else:
                proposals = retrieve(bank, initial[0], jq, remaining,
                    method in ('response_retrieval', 'response_matching_only'),
                    transport=method in ('response_retrieval', 'response_transport_only'))
            final = engine.evaluate(query, [BASE+d for d in proposals], folder/'candidates')
            records = initial+final
            chosen = select_result(records)
            actual = engine.count-start_count
            assert actual == args.budget
            ok, spectral, accents = feasibility(chosen, initial[0])
            row = dict(query=query, method=method, renders=actual,
                       initial_margin=initial[0]['margin'], final_margin=chosen['margin'],
                       margin_gain=chosen['margin']-initial[0]['margin'],
                       changed_controls=int(np.count_nonzero(np.abs(np.array(chosen['z'])-BASE)>1e-8)),
                       centroid_log_drift=spectral, accent_max_drift=accents,
                       preservation_pass=ok,
                       rejected_candidates=sum(not feasibility(r, initial[0])[0] for r in records[1:]),
                       selected_audio=chosen['wav'])
            rows.append(row)
            shutil.copy2(out/chosen['wav'], folder/'selected.wav')
            (folder/'selection.json').write_text(json.dumps(dict(summary=row, selected=chosen,
                proposals=[d.tolist() for d in proposals]), indent=2)+'\n')
            print(f"  proxy gain {row['margin_gain']:+.5f}; changed controls {row['changed_controls']}", flush=True)
    with (out/'summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    import importlib.metadata
    config.update(status='complete', offline_renders=offline_count, total_renders=engine.count,
                  results=rows, script_sha256=hashlib.sha256((out/'script-snapshot.py').read_bytes()).hexdigest(),
                  versions={p: importlib.metadata.version(p) for p in ('numpy', 'torch', 'laion-clap')})
    (out/'report.json').write_text(json.dumps(config, indent=2)+'\n')
    print(f'Completed. Results: {out / "summary.csv"}', flush=True)


if __name__ == '__main__':
    main()
