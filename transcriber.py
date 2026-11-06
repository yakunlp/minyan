"""Local English transcription; uploaded audio is never used as a disk path."""

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Callable

from diarization import SpeakerDiarizer, UNKNOWN_SPEAKER, align_words


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}
MODELS = ("base.en", "small.en")
MODEL_ROOT = Path(__file__).resolve().parent / ".models"


class ModelLoadError(RuntimeError):
    """Model preparation failed before the uploaded audio was decoded."""


class BusyError(RuntimeError):
    """Another browser session is already using the transcription engine."""


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None


@dataclass(frozen=True)
class Transcript:
    segments: tuple[TranscriptSegment, ...]
    duration: float

    @property
    def text(self) -> str:
        return "\n".join(
            f"[{segment.speaker}] {segment.text}" if segment.speaker else segment.text
            for segment in self.segments
        )


def validate_upload(filename: str, size: int) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("不支持此文件格式，请上传 MP3、WAV、M4A、FLAC、OGG 或 AAC。")
    if size <= 0:
        raise ValueError("音频文件为空，请重新选择文件。")
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("音频文件不能超过 50 MB，请先裁剪或压缩。")
    return extension


def create_model(name: str):
    # Lazy import allows lightweight validation/tests without downloading models.
    from faster_whisper import WhisperModel

    local_path = MODEL_ROOT / name
    required = ("config.json", "model.bin", "tokenizer.json")
    local_ready = all((local_path / filename).is_file() for filename in required)
    try:
        return WhisperModel(
            str(local_path) if local_ready else name,
            device="cpu",
            compute_type="int8",
            download_root=str(MODEL_ROOT),
            local_files_only=local_ready,
        )
    except Exception as exc:
        raise ModelLoadError(
            f"英语模型 {name} 下载或加载失败，尚未开始读取你的音频。"
            "请检查模型下载网络或预先安装本地模型；无需因此转换音频格式。"
            "操作方法见项目 README 的“模型下载失败”章节。"
        ) from exc


class TranscriptionService:
    """Share one model and reject overlapping work instead of exhausting memory."""

    def __init__(self, model_factory: Callable = create_model, diarizer_factory: Callable = SpeakerDiarizer):
        self._factory = model_factory
        self._model = None
        self._model_name = None
        self._lock = Lock()
        self._diarizer_factory = diarizer_factory
        self._diarizer = None
        self._speaker_count = None

    def transcribe(
        self,
        audio: bytes,
        filename: str,
        model_name: str = "base.en",
        on_progress: Callable[[float], None] | None = None,
        distinguish_speakers: bool = False,
        num_speakers: int | None = None,
    ) -> Transcript:
        extension = validate_upload(filename, len(audio))
        with TemporaryDirectory(prefix="english-transcribe-") as directory:
            audio_path = Path(directory) / f"audio{extension}"
            audio_path.write_bytes(audio)
            return self._run(
                str(audio_path), model_name, on_progress, distinguish_speakers, num_speakers
            )

    def transcribe_source(
        self,
        source: str,
        model_name: str = "base.en",
        on_progress: Callable[[float], None] | None = None,
        distinguish_speakers: bool = False,
        num_speakers: int | None = None,
    ) -> Transcript:
        """Transcribe a local path or an http(s) media URL (for example a BBC HLS stream).

        The stream is decoded directly by PyAV, so no temporary audio file is
        written for remote sources.
        """
        if not isinstance(source, str) or not source:
            raise ValueError("音频来源应为本地路径或 http(s) 媒体地址。")
        return self._run(source, model_name, on_progress, distinguish_speakers, num_speakers)

    def _run(
        self,
        model_input,
        model_name: str,
        on_progress: Callable[[float], None] | None,
        distinguish_speakers: bool,
        num_speakers: int | None,
    ) -> Transcript:
        if model_name not in MODELS:
            raise ValueError("请选择支持的英语模型。")
        if num_speakers is not None and (
            isinstance(num_speakers, bool) or not isinstance(num_speakers, int)
            or not 1 <= num_speakers <= 10
        ):
            raise ValueError("说话人数应为 1～10 的整数，或使用自动估计。")
        if not self._lock.acquire(blocking=False):
            raise BusyError("电脑正在处理另一个转录任务，请稍后重新点击开始转录。")

        try:
            if distinguish_speakers and (
                self._diarizer is None or self._speaker_count != num_speakers
            ):
                self._diarizer = None
                self._diarizer = self._diarizer_factory(num_speakers)
                self._speaker_count = num_speakers
            if self._model_name != model_name:
                # Release the previous model before loading another one.
                self._model = None
                self._model_name = None
                self._model = self._factory(model_name)
                self._model_name = model_name

            turns = []
            source = model_input
            if distinguish_speakers:
                from faster_whisper.audio import decode_audio

                source = decode_audio(model_input, sampling_rate=16000)
                turns = self._diarizer.process(
                    source,
                    on_progress=(lambda value: on_progress(0.35 * value)) if on_progress else None,
                )
            options = {"word_timestamps": True} if distinguish_speakers else {}
            segments, info = self._model.transcribe(
                source,
                language="en",
                task="transcribe",
                beam_size=5,
                vad_filter=True,
                **options,
            )
            result = []
            # Inference happens during iteration, while any temp file still exists.
            for segment in segments:
                text = segment.text.strip()
                if text:
                    if distinguish_speakers and segment.words:
                        for start, end, word, speaker in align_words(segment.words, turns):
                            if not word.strip():
                                continue
                            if result and result[-1].speaker == speaker:
                                previous = result[-1]
                                result[-1] = TranscriptSegment(
                                    previous.start, end, previous.text + word, speaker
                                )
                            else:
                                result.append(TranscriptSegment(start, end, word.lstrip(), speaker))
                    else:
                        result.append(TranscriptSegment(
                            segment.start, segment.end, text,
                            UNKNOWN_SPEAKER if distinguish_speakers else None,
                        ))
                if on_progress and info.duration > 0:
                    value = max(0.0, segment.end / info.duration)
                    on_progress(min(0.99, 0.35 + 0.65 * value if distinguish_speakers else value))
            return Transcript(tuple(result), info.duration)
        finally:
            self._lock.release()