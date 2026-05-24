from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_pack import make_batch_dir, save_pack
from cooling_rag_mg.pipeline import run_requirements


def main() -> None:
    cfg = get_config()
    requirements = [
        {
            "requirement_id": "R001",
            "stakeholder": "船东代表",
            "requirement_text": "我希望主机冷却水系统运行稳定，不能因为冷却不足影响航行安全。泵和冷却器的配置要有冗余，单台设备故障时，主机仍应具备基本运行能力。",
        }
    ]
    payload = run_requirements(requirements, top_k=4)
    batch = make_batch_dir(cfg.paths.search_results_dir)
    path = save_pack(batch, payload)
    print(path)


if __name__ == "__main__":
    main()
