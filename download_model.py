"""Explicit opt-in download of base.en from the ModelScope community mirror."""

import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

from transcriber import MODEL_ROOT


REPO = "https://modelscope.cn/api/v1/models/Systran/faster-whisper-base.en/repo"
FILES = {"config.json", "model.bin", "tokenizer.json", "vocabulary.txt"}


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    print("Downloading base.en from the ModelScope community mirror.", flush=True)
    with urllib.request.urlopen(
        REPO + "/files?Revision=master&Recursive=true", timeout=30
    ) as response:
        metadata = json.load(response)
    if not metadata.get("Success"):
        raise RuntimeError("Unable to retrieve model file metadata")
    entries = {entry["Path"]: entry for entry in metadata["Data"]["Files"]}
    if not FILES.issubset(entries):
        raise RuntimeError("Model repository is missing required files")
    target = MODEL_ROOT / "base.en"
    target.mkdir(parents=True, exist_ok=True)
    for filename in sorted(FILES):
        entry = entries[filename]
        destination = target / filename
        if destination.is_file() and sha256(destination) == entry["Sha256"]:
            print(f"Already verified: {filename}", flush=True)
            continue
        query = urllib.parse.urlencode(
            {"Revision": entry["Revision"], "FilePath": filename}
        )
        temporary = destination.with_suffix(destination.suffix + ".part")
        print(f"Downloading {filename} ({entry['Size'] / 1024 / 1024:.1f} MB)", flush=True)
        try:
            with urllib.request.urlopen(REPO + "?" + query, timeout=60) as source:
                with temporary.open("wb") as output:
                    received = 0
                    while chunk := source.read(1024 * 1024):
                        output.write(chunk)
                        received += len(chunk)
                        if received % (10 * 1024 * 1024) == 0:
                            print(f"  {received / 1024 / 1024:.0f} MB", flush=True)
            if temporary.stat().st_size != entry["Size"] or sha256(temporary) != entry["Sha256"]:
                raise RuntimeError(f"Integrity check failed for {filename}")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"Verified: {filename}", flush=True)
    print(f"Download complete: {target}", flush=True)


if __name__ == "__main__":
    main()