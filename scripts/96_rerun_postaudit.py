# scripts/96_rerun_postaudit.py
"""审计后的全量重跑，按顺序执行；任何一步失败就停止。日志写到 logs/rerun_postaudit_*.log。
用法：96_rerun_postaudit.py            全部步骤
      96_rerun_postaudit.py 2 3 4 7      只跑指定编号的步骤（按编号顺序）
no-RAG 也重跑：deepseek-chat 已从 deepseek-v3 改为解析到 deepseek-flash，两臂必须用同一模型。
"""
from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E4 = "data/search_results/exp_v4"
STEPS = [
    ["scripts/54_run_pipelines_v3.py", "--rag-only"],
    ["scripts/77_run_v4_rag.py"],
    # deepseek-chat now resolves to deepseek-flash (v3 retired): no-RAG arms must be regenerated
    ["scripts/78_run_v4_norag.py"],
    ["scripts/78q_run_v4_norag_qwen.py"],
    ["scripts/79_evaluate_v4.py"],
    ["scripts/83_grade_c_analysis.py"],
    ["scripts/85_run_random_retrieval_ablation.py"],
    ["scripts/70b_kb_verification_v4.py"],
    ["scripts/71b_paired_conflict_v4.py"],
    ["scripts/59_evaluate_v3.py", "--rag-file", f"{E4}/rag_v4_results.json",
     "--norag-file", f"{E4}/norag_v4_results.json", "--out-dir", f"{E4}/credibility_v4"],
    ["scripts/77q_run_v4_rag_qwen.py"],
]


def main() -> None:
    only = {int(x) for x in sys.argv[1:]} or set(range(len(STEPS)))
    log = ROOT / "logs" / f"rerun_postaudit_{datetime.datetime.now():%Y%m%d_%H%M}.log"
    log.parent.mkdir(exist_ok=True)
    (ROOT / E4 / "credibility_v4").mkdir(parents=True, exist_ok=True)
    for i, step in enumerate(STEPS):
        if i not in only:
            continue
        print(f"[{i}] {' '.join(step)}", flush=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\n===== [{i}] {' '.join(step)} =====\n")
            r = subprocess.run([sys.executable, *step], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            sys.exit(f"step {i} failed (rc={r.returncode}); see {log}; resume with: 96_rerun_postaudit.py <remaining step numbers, starting with {i}>")
    print("all steps done; log:", log)


if __name__ == "__main__":
    main()
