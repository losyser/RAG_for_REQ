from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.convert import convert_docx_to_multigranular


def main() -> None:
    cfg = get_config()
    stats = convert_docx_to_multigranular(
        docx_path=cfg.paths.raw_docx,
        evidence_units_path=cfg.paths.evidence_units_jsonl,
        source_chunks_path=cfg.paths.source_chunks_jsonl,
        evidence_groups_path=cfg.paths.evidence_groups_jsonl,
        review_md_path=cfg.paths.review_md,
    )
    print(stats)
    print("review:", cfg.paths.review_md)


if __name__ == "__main__":
    main()
