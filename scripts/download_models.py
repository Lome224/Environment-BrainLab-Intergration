"""Download the official LAION checkpoint and its text-model assets."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "15")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
# Use standard HTTPS downloads; Xet transport fails through this Mac's proxy.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
# Requests and Hugging Face do not automatically use macOS system proxies.
# Respect the user's existing connection without changing system settings.
for scheme, proxy in urllib.request.getproxies().items():
    if scheme in ("http", "https"):
        os.environ.setdefault(f"{scheme.upper()}_PROXY", proxy)


def main():
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download

    repository = "lukewys/laion_clap"
    filename = "music_audioset_epoch_15_esc_90.14.pt"
    expected_sha256 = "fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd"
    print("Resolving the official LAION release on Hugging Face...", flush=True)
    revision = HfApi().model_info(repository, timeout=20).sha
    path = Path(hf_hub_download(repository, filename, revision=revision, local_dir=ROOT / "models"))
    print("Downloading the RoBERTa text encoder and tokenizer...", flush=True)
    snapshot_download("roberta-base", allow_patterns=["config.json", "vocab.json", "merges.txt", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "model.safetensors"])
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise ValueError("Checkpoint checksum does not match the official release")
    manifest = {"repository": repository, "revision": revision, "filename": filename, "sha256": digest.hexdigest(), "source": f"https://huggingface.co/{repository}/resolve/{revision}/{filename}"}
    (ROOT / "models/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Models downloaded. Run: python scripts/verify_environment.py --clap", flush=True)


if __name__ == "__main__":
    main()
