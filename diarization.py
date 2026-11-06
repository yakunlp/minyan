"""Offline speaker diarization and word-to-speaker alignment, without identity inference."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SPEAKER_MODEL_DIR = Path(__file__).resolve().parent / ".models" / "speakers"
UNKNOWN_SPEAKER = "Speaker unknown"


class DiarizationError(RuntimeError):
    """Speaker separation could not be completed."""


@dataclass(frozen=True)
class SpeakerTurn:
    start: float
    end: float
    speaker: int


def speaker_models_ready() -> bool:
    return all(
        (SPEAKER_MODEL_DIR / name).is_file()
        for name in ("segmentation-3.0.onnx", "nemo_en_titanet_small.onnx")
    )


def align_words(words, turns: list[SpeakerTurn]) -> list[tuple[float, float, str, str]]:
    """Assign each word by greatest temporal overlap, not by sentence content.

    No overlapping turn or an equal overlap tie remains explicitly unknown.
    Number speakers by first chronological appearance, not the cluster ID.
    """
    ordered = sorted(turns, key=lambda turn: (turn.start, turn.end, turn.speaker))
    labels = {}
    for turn in ordered:
        if turn.speaker not in labels:
            labels[turn.speaker] = f"Speaker {len(labels) + 1}"
    result = []
    for word in words:
        scores = {}
        for turn in ordered:
            if turn.start > word.end:
                break
            overlap = max(0.0, min(word.end, turn.end) - max(word.start, turn.start))
            if overlap > 0:
                scores[turn.speaker] = scores.get(turn.speaker, 0.0) + overlap
        speaker = UNKNOWN_SPEAKER
        if scores:
            ranked = sorted(scores, key=scores.get, reverse=True)
            if len(ranked) == 1 or scores[ranked[0]] - scores[ranked[1]] > 1e-6:
                speaker = labels[ranked[0]]
        result.append((word.start, word.end, word.word, speaker))
    return result


class SpeakerDiarizer:
    def __init__(self, num_speakers: int | None = None):
        if not speaker_models_ready():
            raise DiarizationError(
                "说话人模型尚未准备好。请在电脑运行 download_speaker_models.py，"
                "或取消“自动区分说话人”先进行普通转录。"
            )
        try:
            import sherpa_onnx as sherpa

            config = sherpa.OfflineSpeakerDiarizationConfig(
                segmentation=sherpa.OfflineSpeakerSegmentationModelConfig(
                    pyannote=sherpa.OfflineSpeakerSegmentationPyannoteModelConfig(
                        model=str(SPEAKER_MODEL_DIR / "segmentation-3.0.onnx")
                    ),
                    num_threads=2,
                    provider="cpu",
                ),
                embedding=sherpa.SpeakerEmbeddingExtractorConfig(
                    model=str(SPEAKER_MODEL_DIR / "nemo_en_titanet_small.onnx"),
                    num_threads=2,
                    provider="cpu",
                ),
                clustering=sherpa.FastClusteringConfig(
                    num_clusters=num_speakers if num_speakers is not None else -1,
                    threshold=0.5,
                ),
                min_duration_on=0.3,
                min_duration_off=0.5,
            )
            if not config.validate():
                raise RuntimeError("Invalid speaker model configuration")
            self._engine = sherpa.OfflineSpeakerDiarization(config)
        except Exception as exc:
            raise DiarizationError(
                "说话人模型加载失败，请检查 sherpa-onnx 安装及本地模型文件。"
            ) from exc

    def process(self, samples, on_progress: Callable[[float], None] | None = None):
        def callback(done, total):
            if on_progress and total:
                on_progress(min(1.0, done / total))
            return 0

        try:
            if self._engine.sample_rate != 16000:
                raise RuntimeError("Expected a 16 kHz speaker model")
            result = self._engine.process(samples, callback=callback).sort_by_start_time()
            return [SpeakerTurn(turn.start, turn.end, turn.speaker) for turn in result]
        except Exception as exc:
            raise DiarizationError(
                "自动区分说话人失败；请尝试较短、清晰且没有重叠讲话的录音，"
                "或取消该选项先进行普通转录。"
            ) from exc