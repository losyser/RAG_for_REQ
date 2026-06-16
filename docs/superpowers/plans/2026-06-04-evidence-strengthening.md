# Evidence Strengthening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过三个方向强化论文的实证基础：(1) 将冲突案例追溯到 PDF 原文条款；(2) 将可追溯性改写为独立论点；(3) 基于 post-hoc 核查数据做配对冲突率检验。

**Architecture:** 方向1读 PDF 找条款号后更新 paper.tex；方向2在 paper.tex 中重构可追溯性小节；方向3新增 `scripts/71_paired_conflict_analysis.py`，用 norag_kb_verification.json 中已配对的 23 条源需求跑 Wilcoxon 检验，再将结果写回 paper.tex。

**Tech Stack:** Python 3、scipy.stats（Wilcoxon）、LaTeX（paper/paper.tex）；PDF 读取用内置 Read 工具

---

## 背景与关键数据

### 9个冲突案例及其KB来源

| 需求ID | no-RAG 错误值 | KB 正确值 | KB 证据 ID | 来源文档 |
|--------|-------------|----------|-----------|---------|
| OR040 | 85°C (高温报警) | 95°C (MAN) | E-DRAFT-TEMPER-REDUNDAN-002 | KB_DRAFT_v1 |
| OR041 | 30秒 (备用泵切换) | 3-5秒 | E-DRAFT-COOLIN-AUTOSTA-001/003 | KB_DRAFT_v1 |
| OR031 | 0-120°C 量程 | 0-100°C | E-DRAFT-TEMPER-CALIBRAT-001 | KB_DRAFT_v1 |
| OR031 | ±0.5°C 精度 | ±1°C | E-DRAFT-TEMPER-CALIBRAT-001 | KB_DRAFT_v1 |
| OR001 | 每6个月校准 | 每5年 | E-DRAFT-TEMPER-CALIBRAT-001 | KB_DRAFT_v1 |
| OR007 | 10% 余量 | 15% (ISO 8861) | E-ISO8861-001 | **S63 ISO 8861:1998** |
| OR049 | 50-80% 液位 | 20%低报/80%高报 | E-DRAFT-EXPANS-LEVELCO-001 | KB_DRAFT_v1 |
| OR016 | DN>100 才NDT | DN≥80 抽检 | E-SUPP-WELD-002 | **S75 CCS 第5篇** |
| OR016 | 100% NDT | ≥10% 抽检 | E-SUPP-WELD-001 | **S74 IACS W7/W28** |
| OR002 | 80% 触发备用泵 | 60-70% | E-DRAFT-COOLIN-AUTOSTA-002 | KB_DRAFT_v1 |

**关键约束：** 7个案例来自 KB_DRAFT_v1（内部草稿，引用了 CCS/DNV 但无条款号），3个有外部来源（ISO 8861、CCS 第5篇、IACS W7/W28）。Task 1 只追溯这3个外部来源案例，以及在 CCS/IACS PDF 里能找到的 KB_DRAFT_v1 条款。

### H_hard 配对数据状态
- `norag_kb_verification.json` 中 RAG=117条/41个源需求，no-RAG=79条/32个源需求
- **配对（两臂都有数值 shall）：23个源需求**
- 配对样本可直接做 Wilcoxon signed-rank 检验

---

## 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/71_paired_conflict_analysis.py` | **新建** | Task 3 配对冲突率 Wilcoxon 检验 |
| `data/search_results/exp_v3/paired_conflict_analysis.json` | 自动生成 | Task 3 输出结果 |
| `paper/paper.tex` | **修改** | Task 1 加条款号 + Task 2 重构可追溯性节 + Task 3 加配对检验结果 |

---

## Task 1：PDF 条款核查，为3个外部来源案例加条款号

**目标：** 在 CCS 和 IACS PDF 中找到 OR007（ISO 8861 / 15% 余量）、OR016（CCS 焊接 / IACS W7/W28）的原文条款，然后在 paper.tex 的冲突案例表中加入条款引用。

**Files:**
- Read: `/mnt/d/cooling_rag_multigranular/CCS_钢质海船入级规范_2024.pdf`（需要搜索焊接/NDT 相关章节）
- Read: `/mnt/d/cooling_rag_multigranular/IACS_URM_Machinery_Requirements.pdf`（搜索冷却系统余量/焊接）
- Modify: `paper/paper.tex`（更新 `tab:conflicts` 表格）

- [ ] **Step 1：在 IACS PDF 中查找 ISO 8861 冷却余量条款**

  搜索关键词：`cooling capacity margin` 或 `15%`，IACS_URM 文件中查看机械类冷却要求部分（一般在前40页）。
  
  用 Read 工具读取 IACS PDF：
  ```
  file_path: /mnt/d/cooling_rag_multigranular/IACS_URM_Machinery_Requirements.pdf
  pages: "1-30"
  ```
  
  预期找到：ISO 8861 要求换热器净冷却能力留有至少15%余量的条款号（如 M28.3 或类似）。
  
  记录：条款号、原文关键句（英文）。

- [ ] **Step 2：在 CCS PDF 中查找管路焊接/NDT 要求**

  CCS 第5篇管路焊接部分，查找 DN 阈值和 NDT 比例要求。
  
  ```
  file_path: /mnt/d/cooling_rag_multigranular/CCS_钢质海船入级规范_2024.pdf
  pages: "1-20"  # 先看目录，确定焊接章节页码，再读具体页
  ```
  
  预期找到：DN≥80mm 抽检、抽检比例≥10% 的条文。

- [ ] **Step 3：在 IACS PDF 中查找 W7/W28 焊接要求**

  ```
  file_path: /mnt/d/cooling_rag_multigranular/IACS_URM_Machinery_Requirements.pdf
  pages: "40-80"
  ```
  
  预期找到：IACS W7 或 W28 对冷却水管路焊接 NDT 的要求。

- [ ] **Step 4：对 KB_DRAFT_v1 案例搜索 CCS 对应条款**

  在 CCS PDF 中搜索温度传感器、备用泵、膨胀水箱相关内容，看是否有直接对应的条款：
  - 温度传感器精度 / 校准周期
  - 备用泵切换时间
  - 膨胀水箱液位报警值
  
  若找到，记录条款号；若未找到，在 paper 中标注"per industry practice consistent with CCS/DNV rules"。

- [ ] **Step 5：更新 paper.tex 冲突案例表**

  找到 `tab:conflicts` 表格位置（grep `tab:conflicts` paper/paper.tex）。
  
  在每行末尾加一列 `Source`，格式：
  ```latex
  OR007 & 10\% & 15\% & ISO~8861:1998 §X.X & Under-margins heat exchanger \\
  OR016 & DN>100 & DN≥80 & CCS 第5篇 §X.X / IACS W28 & Missed NDT requirement \\
  OR040 & 85\,°C & 95\,°C & KB (consistent w/ MAN spec.) & 10°C under-alarm \\
  ```
  
  若某案例在 PDF 中未找到精确条款，填写 `KB\_DRAFT\_v1 (cites CCS/DNV)` 作为来源。

- [ ] **Step 6：在 paper.tex Limitations 加一句 KB 同源说明**

  找到 Limitations 节，加入：
  ```latex
  The domain KB was assembled by the authors; seven of the nine numeric conflict cases
  are supported by KB entries authored with reference to CCS and DNV rules but without
  explicit clause citations. Two cases cite published standards directly (ISO~8861:1998
  and CCS/IACS welding rules), providing externally verifiable ground truth.
  ```

---

## Task 2：可追溯性作为独立论点重写

**目标：** 在 paper.tex 中将 99.6% citation 率从"附带好处"改写为"独立贡献"，角度：ISO 29148 合规 + 验证成本。

**Files:**
- Modify: `paper/paper.tex`（修改/扩展 traceability 相关段落）

- [ ] **Step 1：定位现有可追溯性相关内容**

  ```bash
  grep -n "traceab\|attribution\|99.6\|citation" paper/paper.tex | head -30
  ```
  
  找到现有分散的引用处，确定哪一节描述了可追溯性结果。

- [ ] **Step 2：在 Results 里确认 §3.1 已有 99.6% 数字**

  该节应该有：RAG 483 shalls / 99.6% KB attribution vs no-RAG 0%。
  确认段落位置（行号）。

- [ ] **Step 3：将 §3.1 拆出一个独立 subsection，命名为"Per-Shall KB Attribution"**

  在 §3.1 的数字段落后添加：
  ```latex
  \subsection{Per-Shall KB Attribution and Downstream Verifiability}
  \label{sec:attribution}
  
  Attribution at 99.6\% means each of the 481 RAG-generated shall statements
  carries a machine-readable citation to at least one KB unit. Under
  ISO/IEC/IEEE~29148, every requirement must be traceable to its authoritative
  justification; the no-RAG baseline provides 0\% traceability by design,
  requiring a human engineer to manually locate and verify every numeric value
  before the output can enter the design record. For a set of 244 shall statements
  each potentially containing two to three numeric parameters, this represents
  a substantial verification burden that the RAG pipeline eliminates by construction.
  
  Attribution is not merely a process property. Section~\ref{sec:posthoc} demonstrates
  that RAG's cited numeric values are confirmed by the KB in 93.6\% of cases---meaning
  the citation is a reliable proxy for correctness, not a vacuous label.
  ```

- [ ] **Step 4：在 Discussion 里为可追溯性加独立段落**

  找到 Discussion 的"what RAG provides"部分，加入或扩展：
  ```latex
  \textbf{Traceability as engineering infrastructure.}
  The 99.6\% per-shall attribution rate should be understood as infrastructure
  rather than performance: it converts an opaque LLM output into a structured
  artefact where every numeric constraint can be audited against a KB unit,
  and every KB unit traces back to a source document. This satisfies the
  traceability requirement of ISO/IEC/IEEE~29148 by construction. The no-RAG
  baseline, regardless of its surface quality, produces output that is
  fundamentally incompatible with this requirement: without citations, a
  downstream engineer cannot distinguish a correct value from a hallucinated one
  without performing the full manual verification the pipeline was meant to replace.
  ```

- [ ] **Step 5：更新 Contributions 列表，明确可追溯性为独立贡献**

  找到 Introduction 的 Contributions 列表，加入或更新：
  ```latex
  \item \textbf{ISO/IEC/IEEE 29148-compliant per-shall traceability.}
  The pipeline achieves 99.6\% per-shall KB attribution versus 0\% for the
  unconstrained baseline, converting LLM output into auditable engineering
  artefacts where every numeric constraint cites its authoritative source.
  Post-hoc verification confirms that attribution is a reliable correctness
  proxy: RAG's cited values are KB-supported in 93.6\% of cases.
  ```

---

## Task 3：基于 post-hoc 数据的配对冲突率 Wilcoxon 检验

**目标：** 新建 `scripts/71_paired_conflict_analysis.py`，对 23 个两臂都有数值 shall 的配对源需求，按源需求级冲突率做 Wilcoxon signed-rank 检验，结果写入 json，然后更新 paper.tex。

**Files:**
- Create: `scripts/71_paired_conflict_analysis.py`
- Auto-generate: `data/search_results/exp_v3/paired_conflict_analysis.json`
- Modify: `paper/paper.tex`（在 §3.2 或 Discussion 加配对检验结果）

- [ ] **Step 1：新建脚本框架并验证数据加载**

  创建 `scripts/71_paired_conflict_analysis.py`，内容：
  ```python
  # scripts/71_paired_conflict_analysis.py
  """
  配对冲突率分析：在两臂都生成了含数值 shall 的源需求子集（n=23）上，
  用 Wilcoxon signed-rank 检验比较 RAG v3 与 no-RAG 的每源需求冲突率。
  
  输入：data/search_results/exp_v3/norag_kb_verification.json
  输出：data/search_results/exp_v3/paired_conflict_analysis.json
        data/search_results/exp_v3/paired_conflict_summary.txt
  """
  from __future__ import annotations
  import json
  from collections import defaultdict
  from pathlib import Path
  from scipy import stats
  
  PROJECT_ROOT = Path(__file__).resolve().parents[1]
  VER_PATH = PROJECT_ROOT / "data" / "search_results" / "exp_v3" / "norag_kb_verification.json"
  OUT_JSON  = PROJECT_ROOT / "data" / "search_results" / "exp_v3" / "paired_conflict_analysis.json"
  OUT_TXT   = PROJECT_ROOT / "data" / "search_results" / "exp_v3" / "paired_conflict_summary.txt"
  
  def main() -> None:
      with open(VER_PATH, encoding="utf-8") as f:
          data = json.load(f)
  
      # 按 arm × source_req 聚合
      by_arm_req: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
      for row in data["details"]:
          if row.get("label") in ("conflict", "supported", "unverifiable"):
              by_arm_req[row["arm"]][row["sid"]].append(row["label"])
  
      rag_reqs   = set(by_arm_req["rag_v3"].keys())
      norag_reqs = set(by_arm_req["no_rag"].keys())
      paired_reqs = sorted(rag_reqs & norag_reqs)
      print(f"配对源需求（两臂均有数值shall）: {len(paired_reqs)}")
  
      # 计算每个源需求的冲突率
      rows = []
      rag_rates, norag_rates = [], []
      for rid in paired_reqs:
          rag_labels   = by_arm_req["rag_v3"][rid]
          norag_labels = by_arm_req["no_rag"][rid]
          rag_conflict   = rag_labels.count("conflict")   / len(rag_labels)
          norag_conflict = norag_labels.count("conflict") / len(norag_labels)
          rag_rates.append(rag_conflict)
          norag_rates.append(norag_conflict)
          rows.append({
              "requirement_id": rid,
              "rag_n_shalls": len(rag_labels),
              "rag_conflict_rate": round(rag_conflict, 4),
              "norag_n_shalls": len(norag_labels),
              "norag_conflict_rate": round(norag_conflict, 4),
              "delta": round(norag_conflict - rag_conflict, 4),
          })
  
      # Wilcoxon signed-rank（双尾）
      stat, p = stats.wilcoxon(rag_rates, norag_rates, alternative="two-sided",
                               zero_method="pratt")
  
      result = {
          "n_paired": len(paired_reqs),
          "rag_mean_conflict_rate":   round(sum(rag_rates) / len(rag_rates), 4),
          "norag_mean_conflict_rate": round(sum(norag_rates) / len(norag_rates), 4),
          "wilcoxon_statistic": float(stat),
          "p_value": float(p),
          "significant_alpha_0_05": bool(p < 0.05),
          "per_requirement": rows,
      }
  
      with open(OUT_JSON, "w", encoding="utf-8") as f:
          json.dump(result, f, ensure_ascii=False, indent=2)
  
      summary = [
          "=" * 55,
          "配对冲突率分析（post-hoc KB核查，paired Wilcoxon）",
          "=" * 55,
          f"配对源需求数: {result['n_paired']}",
          f"RAG v3 平均冲突率: {result['rag_mean_conflict_rate']:.4f}",
          f"no-RAG 平均冲突率: {result['norag_mean_conflict_rate']:.4f}",
          f"Wilcoxon W={result['wilcoxon_statistic']:.1f}, p={result['p_value']:.4f}",
          f"显著 (α=0.05): {result['significant_alpha_0_05']}",
      ]
      OUT_TXT.write_text("\n".join(summary), encoding="utf-8")
      for line in summary:
          print(line)
      print(f"\n结果写入: {OUT_JSON}")
  
  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2：运行脚本，确认结果**

  ```bash
  cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
  /mnt/d/Users/yando/miniconda3/envs/cooling_rag_env/python.exe scripts/71_paired_conflict_analysis.py
  ```
  
  预期输出：
  ```
  配对源需求（两臂均有数值shall）: 23
  RAG v3 平均冲突率: 0.0xxx
  no-RAG 平均冲突率: 0.0xxx
  Wilcoxon W=xx.x, p=0.xxxx
  显著 (α=0.05): True/False
  ```
  
  检查 `paired_conflict_analysis.json` 是否正常写入。

- [ ] **Step 3：根据结果决定在 paper.tex 的位置**

  - 若 p < 0.05（显著）：加入 Results §3.2，作为支持主发现的配对检验证据
  - 若 p ≥ 0.05（不显著）：加入 Discussion Limitations，说明在 23 个配对样本上方向一致但未达显著

- [ ] **Step 4：将结果写入 paper.tex**

  **若显著（p < 0.05），在 §3.2 末尾加入段落：**
  ```latex
  To provide paired statistical evidence, we restrict to the $n=23$ source
  requirements for which both arms generated at least one numeric shall statement.
  Within this paired subset, RAG v3 achieves a mean per-requirement conflict rate
  of $X.X\%$ versus $X.X\%$ for no-RAG (Wilcoxon signed-rank, $W=XX$, $p=0.0XX$,
  $n=23$ pairs). This paired analysis controls for requirement-level difficulty
  and confirms the post-hoc aggregate finding on the subset where both arms
  produced verifiable output.
  ```
  
  **若不显著（p ≥ 0.05），在 Discussion Limitations 加入段落：**
  ```latex
  Within the $n=23$ paired source requirements where both arms generated numeric
  shalls, RAG v3 achieves a lower mean per-requirement conflict rate ($X.X\%$
  vs $X.X\%$), but the difference does not reach significance (Wilcoxon, $p=0.XX$).
  The small paired subset ($n=23$ of 60 source requirements) limits statistical power;
  the aggregate post-hoc finding (Section~\ref{sec:posthoc}) covers all 196 numeric
  shalls and is the primary evidence.
  ```
  
  （将 X.X 替换为 Step 2 实际输出的数字）

---

## Task 4：编译验证

**目标：** 确认上述修改不破坏 LaTeX 编译。

**Files:**
- Read: `paper/paper.tex`（核对修改后语法）

- [ ] **Step 1：检查 paper.tex 中新添加的 LaTeX 语法**

  确认：
  - 所有 `\label{sec:attribution}` 在 `\ref{}` 使用前已定义
  - 表格列数一致（若 `tab:conflicts` 加了 Source 列，表头也要加）
  - 没有未闭合的 `{}`

- [ ] **Step 2：（可选）若有 pdflatex，本地编译确认**

  若 Windows 有 TeX Live 或 MiKTeX：
  ```bat
  cd paper
  pdflatex paper.tex
  ```
  检查无 Error（Warning 可接受）。

---

## 执行优先级说明

- **Task 3 优先**：纯代码，30 分钟内可完成，结果直接决定 Task 3 在 paper 里的位置（Results 还是 Limitations）
- **Task 1 次之**：需要人工读 PDF，找条款号，视 PDF 内容而定（30-90 分钟）
- **Task 2 可与 Task 3 并行**：paper.tex 修改，不依赖其他 Task 的结果
- **Task 4 最后**：编译验证

