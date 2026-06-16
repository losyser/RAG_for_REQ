from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_default_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def normalize_device(value: str | None) -> str:
    if not value:
        return get_default_device()
    value = value.strip().lower()
    if value in {"cuda", "cuda:0", "gpu", "nvidia"}:
        return get_default_device()
    if value == "cpu":
        return "cpu"
    return get_default_device()


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name, "").strip()
    return Path(value) if value else default


@dataclass(frozen=True)
class Paths:
    raw_docx: Path = field(
        default_factory=lambda: _path_from_env(
            "RAW_DOCX_PATH",
            PROJECT_ROOT / "data" / "raw" / "evidence.docx",
        )
    )
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"
    indexes_dir: Path = PROJECT_ROOT / "data" / "indexes"
    search_results_dir: Path = PROJECT_ROOT / "data" / "search_results"
    debug_dir: Path = PROJECT_ROOT / "data" / "debug"

    @property
    def evidence_units_jsonl(self) -> Path:
        v2 = self.processed_dir / "evidence_units_v2.jsonl"
        return v2 if v2.exists() else self.processed_dir / "evidence_units.jsonl"

    @property
    def source_chunks_jsonl(self) -> Path:
        return self.processed_dir / "source_chunks.jsonl"

    @property
    def evidence_groups_jsonl(self) -> Path:
        return self.processed_dir / "evidence_groups.jsonl"

    @property
    def review_md(self) -> Path:
        return self.processed_dir / "multigranular_review.md"


@dataclass(frozen=True)
class ModelConfig:
    embedding_model_path: str = field(default_factory=lambda: os.getenv("BGE_M3_MODEL_PATH", "D:/models/bge-m3"))
    device: str = field(default_factory=lambda: normalize_device(os.getenv("DEVICE")))
    normalize_embeddings: bool = True


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str = field(default_factory=lambda: os.getenv("api_key", os.getenv("DEEPSEEK_API_KEY", "")).strip())
    base_url: str = field(default_factory=lambda: os.getenv("base_url", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).strip())
    model: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    use_requirement_splitter: bool = field(default_factory=lambda: os.getenv("USE_REQUIREMENT_SPLITTER", "1").strip() != "0")
    use_evidence_judge: bool = field(default_factory=lambda: os.getenv("USE_EVIDENCE_JUDGE", "1").strip() != "0")
    temperature: float = field(default_factory=lambda: float(os.getenv("DEEPSEEK_TEMPERATURE", "0.0")))
    max_tokens_split: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS_SPLIT", "1200")))
    max_tokens_judge: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS_JUDGE", "2800")))
    max_tokens_requirement_agent: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS_REQUIREMENT_AGENT", "6000")))
    splitter_review_max_rounds: int = field(default_factory=lambda: int(os.getenv("SPLITTER_REVIEW_MAX_ROUNDS", "3")))
    timeout: float = field(default_factory=lambda: float(os.getenv("DEEPSEEK_TIMEOUT", "60.0")))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def make_client(self) -> "OpenAI":
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)


@dataclass(frozen=True)
class QwenConfig:
    api_key: str = field(default_factory=lambda: os.getenv("QWEN_API_KEY", "").strip())
    base_url: str = field(default_factory=lambda: os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").strip())
    model: str = field(default_factory=lambda: os.getenv("QWEN_MODEL", "qwen-max").strip())
    temperature: float = field(default_factory=lambda: float(os.getenv("QWEN_TEMPERATURE", "0.0")))
    timeout: float = field(default_factory=lambda: float(os.getenv("QWEN_TIMEOUT", "60.0")))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def make_client(self) -> "OpenAI":
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)


@dataclass(frozen=True)
class ErnieConfig:
    api_key: str = field(default_factory=lambda: os.getenv("ERNIE_API_KEY", "").strip())
    base_url: str = field(default_factory=lambda: os.getenv("ERNIE_BASE_URL", "https://qianfan.baidubce.com/v2").strip())
    model: str = field(default_factory=lambda: os.getenv("ERNIE_MODEL", "ernie-4.5-turbo-128k"))
    temperature: float = field(default_factory=lambda: float(os.getenv("ERNIE_TEMPERATURE", "0.0")))
    timeout: float = field(default_factory=lambda: float(os.getenv("ERNIE_TIMEOUT", "60.0")))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def make_client(self) -> "OpenAI":
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)


@dataclass(frozen=True)
class KimiConfig:
    api_key: str = field(default_factory=lambda: os.getenv("KIMI_API_KEY", "").strip())
    base_url: str = field(default_factory=lambda: os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1").strip())
    model: str = field(default_factory=lambda: os.getenv("KIMI_MODEL", "moonshot-v1-8k"))
    temperature: float = field(default_factory=lambda: float(os.getenv("KIMI_TEMPERATURE", "0.3")))
    timeout: float = field(default_factory=lambda: float(os.getenv("KIMI_TIMEOUT", "60.0")))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def make_client(self) -> "OpenAI":
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)


@dataclass(frozen=True)
class AppConfig:
    paths: Paths = field(default_factory=Paths)
    model: ModelConfig = field(default_factory=ModelConfig)
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    qwen: QwenConfig = field(default_factory=QwenConfig)
    ernie: ErnieConfig = field(default_factory=ErnieConfig)
    kimi: KimiConfig = field(default_factory=KimiConfig)


def get_config() -> AppConfig:
    cfg = AppConfig()
    if os.getenv("DEBUG_DEVICE", "0").strip() == "1":
        print(f"[Device] cfg.model.device = {cfg.model.device}")
        try:
            import torch

            print(f"[Device] torch.cuda.is_available() = {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"[Device] GPU name = {torch.cuda.get_device_name(0)}")
        except Exception as exc:
            print(f"[Device] torch unavailable during device check: {exc}")
    cfg.paths.processed_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.indexes_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.search_results_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.debug_dir.mkdir(parents=True, exist_ok=True)
    return cfg
