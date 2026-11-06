"""One-click: fetch the latest BBC News bulletin and save its English transcript.

Run it directly (advanced/optional command-line helper; the desktop icon opens
the web page instead):

    & '.venv\\Scripts\\python.exe' bbc_transcribe.py

BBC audio is copyright-protected; keep the saved transcript for personal,
permitted use only.
"""

import argparse
from datetime import datetime
from pathlib import Path
import sys

import bbc
from transcriber import MODELS, TranscriptionService


DEFAULT_OUTPUT = Path(__file__).resolve().parent / "transcripts"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Fetch and transcribe the latest BBC News bulletin."
    )
    parser.add_argument("--model", choices=MODELS, default="base.en")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--speakers", action="store_true", help="also separate speakers")
    parser.add_argument("--num-speakers", type=int, default=None)
    parser.add_argument("--no-open", action="store_true", help="do not open the saved file")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    print("Fetching the latest BBC News bulletin ...", flush=True)
    try:
        episode = bbc.latest_episode()
    except bbc.BBCError as exc:
        print(f"Could not fetch the latest episode: {exc}", flush=True)
        return 2
    print(f"Episode {episode.pid}: {episode.title} ({episode.broadcast})", flush=True)
    print("正在本地转录，首次运行可能需要下载模型……", flush=True)
    result = TranscriptionService().transcribe_source(
        episode.stream_url,
        args.model,
        distinguish_speakers=args.speakers,
        num_speakers=args.num_speakers,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in episode.title)
    path = args.out / f"BBC-News-{stamp}-{safe}.txt"
    path.write_text(result.text + "\n", encoding="utf-8")
    print(f"Saved transcript: {path}", flush=True)
    if not args.no_open and sys.platform == "win32":
        import os

        os.startfile(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
