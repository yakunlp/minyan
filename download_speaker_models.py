"""Download public sherpa-onnx diarization assets without accounts or tokens."""

import json
from pathlib import Path
import shutil
import tarfile
import urllib.request
import time


MODEL_DIR = Path(__file__).resolve().parent / ".models" / "speakers"
RELEASES = "https://api.github.com/repos/k2-fsa/sherpa-onnx/releases/tags/"
SEGMENTATION = "sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
EMBEDDING = "nemo_en_titanet_small.onnx"


def download_asset(tag: str, name: str, target: Path) -> None:
    with urllib.request.urlopen(RELEASES + tag, timeout=30) as response:
        release = json.load(response)
    asset = next(item for item in release["assets"] if item["name"] == name)
    part = target.with_suffix(target.suffix + ".part")
    try:
        print(f"Downloading {name}: {asset['size'] / 1024 / 1024:.1f} MB", flush=True)
        last_error = None
        for url in (asset["browser_download_url"], asset["url"] + "?download=1"):
            for attempt in range(2):
                try:
                    request = urllib.request.Request(url, headers={"Accept": "application/octet-stream"})
                    with urllib.request.urlopen(request, timeout=30) as source:
                        if "application/json" in source.headers.get("Content-Type", ""):
                            raise RuntimeError("GitHub API returned metadata rather than a model")
                        with part.open("wb") as output:
                            shutil.copyfileobj(source, output, length=1024 * 1024)
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    print(f"Download attempt failed: {type(exc).__name__}", flush=True)
                    time.sleep(1)
            if last_error is None:
                break
        if last_error is not None:
            raise last_error
        if part.stat().st_size != asset["size"]:
            raise RuntimeError(f"Incomplete download: {name}")
        # Historical release assets have no published SHA-256. Check size over
        # HTTPS, but do not describe this as cryptographic integrity verification.
        part.replace(target)
    finally:
        part.unlink(missing_ok=True)


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    download_asset("speaker-segmentation-models", SEGMENTATION, MODEL_DIR / SEGMENTATION)
    # Copy only expected regular files; never extract archive-controlled paths.
    prefix = "sherpa-onnx-pyannote-segmentation-3-0/"
    with tarfile.open(MODEL_DIR / SEGMENTATION, "r:bz2") as archive:
        for name in ("model.onnx", "LICENSE", "README.md"):
            member = archive.getmember(prefix + name)
            if not member.isfile() or member.size > 30 * 1024 * 1024:
                raise RuntimeError(f"Unexpected archive member: {name}")
            source = archive.extractfile(member)
            destination = "segmentation-3.0.onnx" if name == "model.onnx" else name
            with source, (MODEL_DIR / destination).open("wb") as output:
                shutil.copyfileobj(source, output)
    download_asset("speaker-recongition-models", EMBEDDING, MODEL_DIR / EMBEDDING)
    print(f"Speaker models ready: {MODEL_DIR}", flush=True)
    print("Read the supplied LICENSE and upstream model licenses before redistribution.", flush=True)


if __name__ == "__main__":
    main()