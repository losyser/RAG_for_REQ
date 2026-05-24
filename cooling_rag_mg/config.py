from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import torch
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_default_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def normalize_device(value: str | None) -> str:
    if not value:
        return get_default_device()
    value = value.strip().lower()
    if value in {"cuda", "cuda:0", "gpu", "nvidia"}:
        return "cuda" if torch.cuda.is_available() else "cpu"
    if value == "cpu":
        return "cpu"
    return get_default_device()


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name, "").strip()
    return Path(value) if value else default


@dataclass(frozen=True)
class Paths:
    raw_docx: Path = _path_from_env(
        "RAW_DOCX_PATH",
        PROJECT_ROOT / "data" / "raw" / "evidence.docx",
    )
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"
    indexes_dir: Path = PROJECT_ROOT / "data" / "indexes"
    search_results_dir: Path = PROJECT_ROOT / "data" / "search_results"
    debug_dir: Path = PROJECT_ROOT / "data" / "debug"

    @property
    def evidence_units_jsonl(self) -> Path:
        return self.processed_dir / "evidence_units.jsonl"

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
    embedding_model_path: str = os.getenv("BGE_M3_MODEL_PATH", "D:/models/bge-m3")
    device: str = normalize_device(os.getenv("DEVICE"))
    normalize_embeddings: bool = True


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str = os.getenv("api_key", os.getenv("DEEPSEEK_API_KEY", "")).strip()
    base_url: str = os.getenv("base_url", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).strip()
    model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    use_requirement_splitter: bool = os.getenv("USE_REQUIREMENT_SPLITTER", "1").strip() != "0"
    use_evidence_judge: bool = os.getenv("USE_EVIDENCE_JUDGE", "1").strip() != "0"
    temperature: float = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.1"))
    max_tokens_split: int = int(os.getenv("MAX_TOKENS_SPLIT", "1200"))   # 900→1200，给更长的拆分结果留余量
    max_tokens_judge: int = int(os.getenv("MAX_TOKENS_JUDGE", "2800"))   # 2200→2800，候选多时 judge 不截断
    max_tokens_requirement_agent: int = int(os.getenv("MAX_TOKENS_REQUIREMENT_AGENT", "6000"))  # 3600→6000，防止复杂需求 JSON 截断


    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


@dataclass(frozen=True)
class AppConfig:
    paths: Paths = Paths()
    model: ModelConfig = ModelConfig()
    deepseek: DeepSeekConfig = DeepSeekConfig()


def get_config() -> AppConfig:
    cfg = AppConfig()
    if os.getenv("DEBUG_DEVICE", "0").strip() == "1":
        print(f"[Device] cfg.model.device = {cfg.model.device}")
        print(f"[Device] torch.cuda.is_available() = {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"[Device] GPU name = {torch.cuda.get_device_name(0)}")
    cfg.paths.processed_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.indexes_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.search_results_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.debug_dir.mkdir(parents=True, exist_ok=True)
    return cfg
