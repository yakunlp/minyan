"""Fetch the latest BBC News bulletin (World Service) and its audio stream.

The BBC programme pages and the public media selector are used exactly as the
website does. BBC audio is copyright-protected; keep any downloaded stream for
personal, permitted use only and never redistribute it.

Two URLs are resolved for each episode: an HLS playlist that PyAV decodes for
transcription, and a plain MP3 that the web page plays in the browser.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import urllib.request


PROGRAMME_PID = "p002vsmz"
PLAYER_URL = f"https://www.bbc.co.uk/programmes/{PROGRAMME_PID}/episodes/player"
PROGRAMME_URL = "https://www.bbc.co.uk/programmes/{pid}.json"
MEDIA_URL = (
    "https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/"
    "vpid/{vpid}/format/json"
)
# The same selector exposes a plain MP3 via its "redir" route. Browsers can play
# it directly (unlike the HLS playlist, which only PyAV decodes here).
DOWNLOAD_URL = (
    "https://open.live.bbc.co.uk/mediaselector/6/redir/version/2.0/"
    "mediaset/audio-nondrm-download/proto/https/vpid/{vpid}.mp3"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) newstranscribe/1.0"}
TIMEOUT = 30
# Episode blocks in the listing HTML expose the pid as data-pid="<pid>".
_DATA_PID = re.compile(r'data-pid="([bpw][0-9a-z]{7,})"')
# Saved bulletins live here. The file name states which episode it is, so the
# audio keeps working after the time-limited BBC URL expires.
DOWNLOAD_DIR = Path(__file__).resolve().parent / "bbc_downloads"


class BBCError(RuntimeError):
    """The latest BBC episode or one of its audio streams could not be retrieved."""


@dataclass(frozen=True)
class BBCEpisode:
    pid: str
    title: str
    broadcast: str
    stream_url: str
    download_url: str


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def _get_text(url: str) -> str:
    return _fetch(url).decode("utf-8", "replace")


def _get_json(url: str) -> dict:
    return json.loads(_fetch(url).decode("utf-8", "replace"))


def parse_episode_pids(html: str) -> list[str]:
    """Return episode ids in document order (newest first), without duplicates.

    The listing page renders one ``data-pid`` attribute per episode block, in
    descending broadcast order, so the first id is the most recent bulletin.
    """
    pids: list[str] = []
    for match in _DATA_PID.finditer(html):
        pid = match.group(1)
        if pid != PROGRAMME_PID and pid not in pids:
            pids.append(pid)
    return pids


def select_audio_href(media: dict) -> str:
    """Choose an HTTPS audio URL (preferring HLS) from a mediaselector response."""
    fallback = None
    for item in media.get("media", []):
        if item.get("kind") != "audio":
            continue
        for connection in item.get("connection", []):
            href = connection.get("href")
            if not href or connection.get("protocol") != "https":
                continue
            if connection.get("transferFormat") == "hls":
                return href
            fallback = fallback or href
    if fallback:
        return fallback
    raise BBCError("BBC 没有为该期返回可用的音频流（可能已过期或版权受限）。")


def build_episode(pid: str) -> BBCEpisode:
    """Resolve one episode id to its title, broadcast date and audio URLs.

    A programme can expose several versions, and only the version that has
    media can be played. The first version is not always the published one, so
    each version is tried until one returns an audio stream.
    """
    try:
        info = _get_json(PROGRAMME_URL.format(pid=pid))
        programme = info["programme"]
    except BBCError:
        raise
    except Exception as exc:
        raise BBCError("无法获取该期 BBC 节目的音频信息，请稍后重试。") from exc
    display = programme.get("display_title") or {}
    title = display.get("subtitle") or programme.get("title") or pid
    broadcast = programme.get("first_broadcast_date") or ""
    versions = [v.get("pid") for v in programme.get("versions", []) if v.get("pid")]
    if not versions:
        raise BBCError("无法获取该期 BBC 节目的音频信息，请稍后重试。")
    last_error: Exception | None = None
    for vpid in versions:
        try:
            media = _get_json(MEDIA_URL.format(vpid=vpid))
            stream_url = select_audio_href(media)
        except Exception as exc:  # noqa: BLE001 - fall through to the next version
            last_error = exc
            continue
        return BBCEpisode(
            pid, title, broadcast, stream_url, DOWNLOAD_URL.format(vpid=vpid)
        )
    raise BBCError(
        "BBC 没有为该期返回可用的音频流（可能已过期或版权受限）。"
    ) from last_error


def latest_episode() -> BBCEpisode:
    """Return the most recent available bulletin with a usable audio stream."""
    try:
        html = _get_text(PLAYER_URL)
    except Exception as exc:
        raise BBCError("无法访问 BBC 节目列表，请检查网络后重试。") from exc
    pids = parse_episode_pids(html)
    if not pids:
        raise BBCError("未能从 BBC 节目列表解析出剧集，页面结构可能已变化。")
    return build_episode(pids[0])


def episode_slug(episode: BBCEpisode) -> str:
    """A filesystem-safe stamp that states which bulletin a file belongs to.

    ``broadcast`` looks like ``2026-11-04T14:00:00Z`` and is turned into
    ``2026-11-04_1400``; when it is missing, the title is sanitised instead.
    """
    match = re.match(r"(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})", episode.broadcast or "")
    if match:
        return f"{match.group(1)}_{match.group(2)}{match.group(3)}"
    safe = "".join(c if c.isalnum() else "-" for c in (episode.title or episode.pid))
    return safe.strip("-") or episode.pid


def download_audio(episode: BBCEpisode, directory: Path = DOWNLOAD_DIR) -> Path:
    """Download the episode's playable MP3 and return its local path.

    The BBC URL is time-limited and requires every playback device to reach BBC,
    so the file is saved once and then served by this app to the computer and the
    phone. The ``.part`` file is replaced only after a non-empty download.
    """
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"BBC-News-{episode_slug(episode)}-{episode.pid}.mp3"
    part = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(episode.download_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as source, part.open(
            "wb"
        ) as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
        if part.stat().st_size == 0:
            raise BBCError("下载到的 BBC 音频为空，请稍后重试。")
        part.replace(target)
    except BBCError:
        raise
    except Exception as exc:
        raise BBCError(
            "下载 BBC 音频失败，可能是网络受限或该期已过期，请稍后重试。"
        ) from exc
    finally:
        part.unlink(missing_ok=True)
    return target


def save_transcript(
    episode: BBCEpisode, text: str, directory: Path = DOWNLOAD_DIR
) -> Path:
    """Save the English transcript next to its audio, labelled with the episode."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"BBC-News-{episode_slug(episode)}-{episode.pid}.txt"
    header = "\n".join(
        (
            "来源：BBC News（BBC World Service 5 分钟新闻简报）",
            f"期号：{episode.title}",
            f"播出时间：{episode.broadcast or '未知'}",
            f"节目编号：{episode.pid}",
            "-" * 40,
            "",
        )
    )
    target.write_text(header + text.strip() + "\n", encoding="utf-8")
    return target
