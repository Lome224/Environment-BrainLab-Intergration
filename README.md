# BrainLab semantic control

Independent Python workspace for Salome's research on sparse, interpretable musical control.

## Setup status

- Verified: Python 3.10.21, Csound rendering and WAV reading, CMA-ES optimization, and imports for CLAP, Transformers, librosa, and Jupyter.
- Verified: VS Code's interpreter and integrated terminal both use `brainlab-semantic`.
- All installed packages pass `pip check`; exact versions are in `requirements-lock.txt`.
- Verified: official music CLAP checkpoint and RoBERTa assets downloaded, with SHA-256 checks against the published file hashes.
- Verified: end-to-end CLAP inference on CPU with network access disabled. The synthetic electronic-tone clip scored 0.4079 for electronic musical tones and 0.0248 for dog barking. These scores demonstrate a working installation, not research validity.
- The first verification used the CPU. Apple GPU execution has not been validated.

## Start here

VS Code is configured for the dedicated `brainlab-semantic` Mamba environment.
Open a new integrated terminal in this project. Then run:

```sh
python scripts/verify_environment.py
python scripts/download_models.py
python scripts/verify_environment.py --clap
```

The first command renders a short synthetic Csound example, reads it, and checks CMA-ES on a mathematical objective. The download command obtains the official music CLAP weights and text-model assets; it requires access to huggingface.co. The final command loads that checkpoint and computes audio–text scores. These are environment checks, not research results or a validated BrainLab integration.

Results appear in `runs/environment-check/`. CLAP uses the CPU for the reproducible initial check; Apple GPU availability is reported separately.

The model files are now cached, so routine checks need only `python scripts/verify_environment.py --clap`. To explicitly check offline operation, run `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python scripts/verify_environment.py --clap`.

The downloader respects this Mac's existing system proxy and uses standard HTTPS. Interrupted downloads can be resumed by rerunning it. No system proxy settings were changed.

## Project layout

- `scripts/`: setup verification and later experiment entry points
- `src/brainlab_semantic/`: your future algorithm modules
- `configs/`: future experiment settings
- `notebooks/`: exploratory analysis
- `models/`: downloaded model weights, excluded from Git
- `runs/`: original and selected audio with Csound sources, included in Git
- `work/` and `.cache/`: temporary files and local caches, excluded from Git

## Environment

Python 3.10 in a dedicated Mamba environment. Csound is a separate executable; the verification script records its version. Python packages and a full lock file are saved in the project after verification.

To recreate the Python environment:

```sh
mamba env create -f environment.yml
mamba run -n brainlab-semantic python -m pip install -r requirements-lock.txt
```

The VS Code interpreter path is specific to this Mac and should be changed on another computer.

## Research boundary

The controls, valid ranges, structural invariants, and BrainLab rendering adapter will be established with Dr. B and Mateo. The demo Csound instrument is solely for verifying installation. Algorithm design, implementation, comparisons, and evaluation belong in this independent workspace.

Model source: https://github.com/LAION-AI/CLAP

Checkpoint: `music_audioset_epoch_15_esc_90.14.pt`, from the LAION CLAP release linked by its authors. Keep its checksum and download provenance in `models/manifest.json`.
