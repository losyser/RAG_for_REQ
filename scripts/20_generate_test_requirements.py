# -*- coding: utf-8 -*-
"""
Script 20: Generate 20 diverse raw requirements for experimental evaluation.

Usage:
    python scripts/20_generate_test_requirements.py
    python scripts/20_generate_test_requirements.py --overwrite
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.requirement_generator import generate_test_requirements


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-generate even if output file already exists")
    args = parser.parse_args()

    cfg = get_config()
    output_path = cfg.paths.processed_dir / "test_requirements.jsonl"

    reqs = generate_test_requirements(
        evidence_units_path=cfg.paths.evidence_units_jsonl,
        output_path=output_path,
        overwrite=args.overwrite,
    )
    print(f"\nDone: {len(reqs)} test requirements → {output_path}")


if __name__ == "__main__":
    main()
