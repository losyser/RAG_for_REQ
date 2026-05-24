from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.index_store import build_index


def main() -> None:
    cfg = get_config()
    build_index(
        jsonl_path=cfg.paths.source_chunks_jsonl,
        output_dir=cfg.paths.indexes_dir / "source_chunks",
        text_field="search_text",
        model_path=cfg.model.embedding_model_path,
        device=cfg.model.device,
        normalize=cfg.model.normalize_embeddings,
    )
    build_index(
        jsonl_path=cfg.paths.evidence_units_jsonl,
        output_dir=cfg.paths.indexes_dir / "evidence_units",
        text_field="search_text",
        model_path=cfg.model.embedding_model_path,
        device=cfg.model.device,
        normalize=cfg.model.normalize_embeddings,
    )
    print("indexes built:", cfg.paths.indexes_dir)


if __name__ == "__main__":
    main()
