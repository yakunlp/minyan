"""Responsive LAN web UI for local English audio transcription."""

import hmac
import logging
from pathlib import Path
import time

import streamlit as st

import bbc
from diarization import DiarizationError, speaker_models_ready
from phoneqr import DEFAULT_PORT, phone_url, qr_png

from transcriber import (
    BusyError,
    MODELS,
    ModelLoadError,
    SUPPORTED_EXTENSIONS,
    TranscriptionService,
    validate_upload,
)


logger = logging.getLogger(__name__)
st.set_page_config(page_title="英语新闻转录工具", page_icon="🎧", layout="centered")


@st.cache_resource
def get_service() -> TranscriptionService:
    return TranscriptionService()


def current_phone_url() -> str | None:
    """The LAN URL for this page, using the port Streamlit is actually on."""
    try:
        port = int(st.get_option("server.port"))
    except Exception:  # noqa: BLE001 - fall back to the project default
        port = DEFAULT_PORT
    return phone_url(port)


def get_secret(name: str):
    """Read an optional secret; a missing secrets file or key simply returns None."""
    try:
        return st.secrets[name]
    except Exception:  # noqa: BLE001 - no secrets configured is normal
        return None


def password_guard() -> None:
    """Require a password only when one is configured (for private/online use).

    A short code is fine because a bookmarked "remember this device" link
    (``?k=<password>``) lets the owner skip typing on a phone entirely.
    """
    expected = get_secret("password")
    if not expected or st.session_state.get("authenticated"):
        return

    # Auto-login from a bookmarked link, so a phone never has to type anything.
    try:
        token = st.query_params.get("k")
    except Exception:  # noqa: BLE001 - query params unavailable is not fatal
        token = None
    if token and hmac.compare_digest(str(token), str(expected)):
        st.session_state.authenticated = True
        return

    st.title("🎧 英语新闻转录工具")
    st.caption("此部署已设置访问口令，请输入后使用。")
    entered = st.text_input("访问口令", type="password")
    remember = st.checkbox("记住这台设备（把本页加入书签，下次免输入）")
    if st.button("进入", type="primary"):
        if hmac.compare_digest(str(entered), str(expected)):
            st.session_state.authenticated = True
            st.session_state.pop("login_failures", None)
            if remember:
                try:
                    st.query_params["k"] = str(expected)
                except Exception:  # noqa: BLE001 - best effort only
                    pass
            st.rerun()
        else:
            failures = st.session_state.get("login_failures", 0) + 1
            st.session_state.login_failures = failures
            # Slow repeated guessing; only this session waits, others are unaffected.
            time.sleep(min(5, max(0, failures - 2)))
            st.error("口令不正确。")
    st.stop()


def logout_control() -> None:
    """Offer a logout button whenever the password gate is active."""
    if get_secret("password") and st.session_state.get("authenticated"):
        if st.sidebar.button("退出登录"):
            st.session_state.authenticated = False
            st.rerun()


def is_local_request() -> bool:
    """True when the page is served from this PC/LAN, so the phone hint helps.

    On a public host (for example Streamlit Community Cloud) the LAN address is
    meaningless, so the phone hint and QR are hidden there.
    """
    try:
        host = str(st.context.headers.get("Host", "")).split(":")[0].lower()
    except Exception:  # noqa: BLE001 - outside the Streamlit runtime / in tests
        return True
    if not host or host in ("localhost", "127.0.0.1"):
        return True
    parts = host.split(".")
    if len(parts) == 4 and all(part.isdigit() for part in parts):
        first, second = int(parts[0]), int(parts[1])
        return (
            first == 10
            or (first == 172 and 16 <= second <= 31)
            or (first == 192 and second == 168)
        )
    return False


def clear_result() -> None:
    for key in (
        "transcript",
        "result_name",
        "elapsed",
        "editable_text",
        "source_note",
        "bbc_episode",
        "bbc_audio_path",
        "bbc_text_path",
    ):
        st.session_state.pop(key, None)


def store_result(result, name: str, started: float, source_note: str | None = None) -> None:
    """Keep one transcript in session state for display, editing and download."""
    st.session_state.transcript = result
    st.session_state.result_name = name
    st.session_state.elapsed = time.monotonic() - started
    st.session_state.editable_text = result.text
    if source_note:
        st.session_state.source_note = source_note


def show_episode_info(episode) -> None:
    """Announce which bulletin is being handled, before any download starts."""
    st.markdown(
        f"**📡 正在下载的最新一期**：{episode.title}  \n"
        f"播出时间：{episode.broadcast or '未知'} · 节目编号：`{episode.pid}`"
    )


def show_episode(episode, audio_path=None, text_path=None) -> None:
    """Show which BBC episode was fetched and play it from the saved copy.

    The saved file is served by this app, so the computer and the phone can both
    play it, and it keeps working after the time-limited BBC URL expires.
    """
    lines = [
        f"**📡 已抓取并保存的一期**：{episode.title}",
        f"播出时间：{episode.broadcast or '未知'} · 节目编号：`{episode.pid}`",
    ]
    saved = Path(audio_path) if audio_path else None
    playable = saved is not None and saved.is_file()
    if playable:
        lines.append(f"音频已保存到电脑：`{saved}`（手机通过本网页播放）")
    if text_path:
        lines.append(f"文本已保存到电脑：`{text_path}`")
    st.markdown("  \n".join(lines))
    if playable:
        # Bytes are delivered by the Streamlit server, so the phone both plays
        # and downloads the saved file through this app, never through BBC.
        audio_bytes = saved.read_bytes()
        st.audio(audio_bytes, format="audio/mp3")
        st.download_button(
            "⬇️ 下载这一期 MP3（手机、电脑都可保存）",
            data=audio_bytes,
            file_name=saved.name,
            mime="audio/mpeg",
            key="bbc_audio_download",
        )
    else:
        # Fall back to the temporary BBC link whenever nothing was saved.
        st.audio(episode.download_url)


password_guard()
logout_control()

st.title("🎧 英语新闻转录工具")
st.write("上传英文音频，生成英文文本。手机、电脑均可使用，不需要付费 API。")
st.caption("音频由运行本网页的电脑处理，不发送到云端识别服务。")

# On this PC/LAN, show the address and a QR so a phone can open the page. On a
# public host (cloud) the LAN address is meaningless, so it is hidden there.
if is_local_request():
    phone = current_phone_url()
    if phone:
        st.markdown(
            f"📱 **手机访问**：[{phone}]({phone})（手机与电脑连同一 Wi-Fi；"
            "电脑保持开机，本服务窗口不要关）"
        )
        qr = qr_png(phone)
        if qr:
            st.image(qr, width=170, caption="手机相机或“扫一扫”扫码即可直接打开本页")
    else:
        st.caption("📱 手机访问：让手机与电脑连同一 Wi-Fi，用电脑无线 IPv4 加 `:8501` 打开。")

with st.expander("使用说明与隐私"):
    st.markdown(
        "- 支持 MP3、WAV、M4A、FLAC、OGG、AAC，每个文件最多 **50 MB**。\n"
        "- 建议先用 1～3 分钟的音频测试；长音频可能需要较长时间和较多内存。\n"
        "- 首次使用每个模型需要联网下载，请耐心等待。后续复用本地缓存。\n"
        "- 转录期间请保持页面打开、电脑开机；刷新或断线可能丢失页面结果。\n"
        "- 临时音频正常完成或报错后自动删除；上传内容和结果在会话内存中暂存。\n"
        "- 本地使用时请仅在可信的家庭局域网内使用；若部署到公网（如云端），务必设置访问口令（secret `password`），并自行评估版权与隐私责任。\n"
        "- 转录可能有误，尤其是人名、数字和背景音乐，请结合原音频校对。"
    )

uploaded = st.file_uploader(
    "选择英文音频",
    type=sorted(extension.lstrip(".") for extension in SUPPORTED_EXTENSIONS),
    key="audio_upload",
    on_change=clear_result,
)
model_name = st.selectbox(
    "识别模型",
    MODELS,
    format_func=lambda name: {
        "base.en": "快速模式 · base.en（建议先试用）",
        "small.en": "精细模式 · small.en（更慢，需要更多内存）",
    }[name],
    on_change=clear_result,
)
distinguish_speakers = st.checkbox(
    "自动区分说话人（本地处理，无需账号）",
    value=False,
    on_change=clear_result,
    help="默认关闭，按普通方式转录。需要区分发言人时再勾选，会额外耗时并需要已下载的说话人模型。",
)
num_speakers = None
if distinguish_speakers:
    count = st.selectbox(
        "说话人数",
        ["自动估计", *range(1, 11)],
        on_change=clear_result,
        help="知道人数时指定通常更稳定；自动估计可能把同一人拆开或将不同人合并。",
    )
    num_speakers = None if count == "自动估计" else count
    st.caption(
        "Speaker 1 / Speaker 2 按首次出现排序，不代表真实姓名。"
        "重叠讲话、短句、音乐和口音可能导致误分，无法匹配的词会标记 Speaker unknown。"
        "分离进度约占前 35%，转录占后 65%，不是耗时预测。"
    )
    if not speaker_models_ready():
        st.warning("说话人模型未安装：在电脑运行 download_speaker_models.py，或取消此选项普通转录。")

valid_upload = False
if uploaded is not None:
    try:
        validate_upload(uploaded.name, uploaded.size)
        valid_upload = True
        st.caption(f"已选择：{uploaded.name} · {uploaded.size / 1024 / 1024:.2f} MB")
        st.audio(uploaded)
    except ValueError as exc:
        st.error(str(exc))

if st.button("开始转录", type="primary", disabled=not valid_upload):
    clear_result()
    progress = st.progress(0.0, text="准备模型（首次使用会下载），随后开始识别……")
    started = time.monotonic()
    try:
        with st.spinner("正在本地处理，请保持页面打开……"):
            result = get_service().transcribe(
                uploaded.getvalue(),
                uploaded.name,
                model_name,
                on_progress=lambda value: progress.progress(
                    value, text=f"处理进度约 {value:.0%}（不是剩余时间估算）"
                ),
                distinguish_speakers=distinguish_speakers,
                num_speakers=num_speakers,
            )
        progress.progress(1.0, text="处理完成")
        if result.text:
            # Uploaded name is used only as a suggested download name, never as a server path.
            store_result(result, Path(uploaded.name).stem + ".txt", started)
        else:
            st.warning("没有识别到有效语音，请确认文件包含清晰的英语讲话。")
    except BusyError as exc:
        progress.empty()
        st.warning(str(exc))
    except ModelLoadError as exc:
        progress.empty()
        logger.exception("Model preparation failed")
        st.error(str(exc))
    except DiarizationError as exc:
        progress.empty()
        logger.exception("Speaker diarization failed")
        st.error(str(exc))
    except Exception:
        progress.empty()
        logger.exception("Local transcription failed")
        st.error(
            "转录失败。请确认音频能够正常播放，并尝试较短的 MP3/WAV 文件。"
            "首次运行还需检查模型下载网络及电脑可用内存；详细错误见电脑终端。"
        )

st.divider()
st.subheader("📡 一键抓取 BBC News")
st.caption(
    "自动获取 BBC World Service 最新的 5 分钟新闻简报，把这一期的音频和英文文本保存到电脑，"
    "并在下方写明具体是哪一期；音频由本网页提供，电脑和手机都能回放。"
    "音频来自 BBC 公开节目页，受版权保护，请仅用于你有权使用的个人场景，不要再次分发。"
)
start_button = st.button("📡 抓取并转录最新 BBC News", type="secondary")
# One stable slot so the episode info can appear the moment it is fetched and
# then be refreshed in place once the audio and transcript are saved.
episode_slot = st.empty()
if start_button:
    clear_result()
    progress = st.progress(0.0, text="正在获取 BBC 最新一期简报……")
    started = time.monotonic()
    try:
        with st.spinner("正在获取 BBC 最新节目信息……"):
            episode = bbc.latest_episode()
        # Announce which bulletin this is *before* downloading and transcribing,
        # so the user does not have to wait for the transcript to know the date.
        st.session_state.bbc_episode = episode
        with episode_slot.container():
            show_episode_info(episode)
        progress.progress(
            0.03, text=f"最新一期：{episode.title}（{episode.broadcast or '时间未知'}）"
        )
        # Save the audio first, then transcribe that saved copy. This requests
        # the bulletin only once and keeps a local file the phone can replay.
        audio_source = episode.stream_url
        with st.spinner("正在把这一期音频下载到电脑……"):
            try:
                audio_path = bbc.download_audio(episode)
            except bbc.BBCError as exc:
                logger.warning("Saving BBC audio failed: %s", exc)
                st.info("未能把音频保存到电脑，改用在线流直接转录（本次不保存本地文件）。")
            else:
                st.session_state.bbc_audio_path = str(audio_path)
                audio_source = str(audio_path)
        progress.progress(0.08, text="开始本地转录，请保持页面打开……")
        with st.spinner("正在本地转录，请保持页面打开……"):
            result = get_service().transcribe_source(
                audio_source,
                model_name,
                on_progress=lambda value: progress.progress(
                    min(0.99, 0.08 + 0.92 * value),
                    text=f"处理进度约 {value:.0%}（不是剩余时间估算）",
                ),
                distinguish_speakers=distinguish_speakers,
                num_speakers=num_speakers,
            )
        progress.progress(1.0, text="处理完成")
        if result.text:
            try:
                text_path = bbc.save_transcript(episode, result.text)
            except OSError as exc:
                logger.warning("Saving BBC transcript failed: %s", exc)
            else:
                st.session_state.bbc_text_path = str(text_path)
            store_result(
                result,
                f"BBC-News-{bbc.episode_slug(episode)}.txt",
                started,
                source_note=f"来源：BBC News · {episode.title}（{episode.broadcast}）",
            )
        else:
            st.warning("没有识别到有效语音，请稍后重试。")
    except bbc.BBCError as exc:
        progress.empty()
        logger.exception("BBC episode fetch failed")
        st.error(str(exc))
    except BusyError as exc:
        progress.empty()
        st.warning(str(exc))
    except ModelLoadError as exc:
        progress.empty()
        logger.exception("Model preparation failed")
        st.error(str(exc))
    except DiarizationError as exc:
        progress.empty()
        logger.exception("Speaker diarization failed")
        st.error(str(exc))
    except Exception as exc:
        progress.empty()
        logger.exception("BBC transcription failed")
        st.error(
            "抓取或转录 BBC 音频失败。请检查网络连接后重试；"
            "若刚更新过代码，请重启网页服务（旧进程不会自动加载新模块）。"
            f"\n\n技术信息：{type(exc).__name__}: {exc}"
        )


if st.session_state.get("bbc_episode") is not None:
    with episode_slot.container():
        show_episode(
            st.session_state.bbc_episode,
            st.session_state.get("bbc_audio_path"),
            st.session_state.get("bbc_text_path"),
        )


if "transcript" in st.session_state:
    result = st.session_state.transcript
    if st.session_state.get("source_note"):
        st.caption(st.session_state.source_note)
    st.success(f"转录完成，用时 {st.session_state.elapsed:.1f} 秒。")
    st.subheader("英文文本")
    text = st.text_area(
        "可以直接校对和编辑，下载文件会包含你的修改；也可全选复制。",
        key="editable_text",
        height=320,
    )
    st.download_button(
        "下载英文 TXT",
        data=text.encode("utf-8"),
        file_name=st.session_state.result_name,
        mime="text/plain; charset=utf-8",
    )
    with st.expander("查看原始时间戳（秒）"):
        st.dataframe(
            [
                {"开始": round(s.start, 2), "结束": round(s.end, 2),
                 "说话人": s.speaker or "未启用", "原文": s.text}
                for s in result.segments
            ],
            hide_index=True,
            use_container_width=True,
        )

st.caption("仅限你有权处理的音频。本工具生成的是英文转录，不是中文翻译。")