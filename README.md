# Multi-Granular RAG for Ship Cooling Water Requirements

Reference implementation for the paper:

> *Multi-Granular Retrieval-Augmented Generation for Evidence-Based Engineering Requirement Formulation in Ship Cooling Systems* (JMSE, 2026).

## Reproducing the paper

Every number in Tables 3–9 of the paper is traceable to a `batch_*/experiment/manifest.json` file containing the exact DeepSeek model version returned by the API, all hyperparameters, random seeds, and dependency versions.

**Fast path (cached replay, no API key required, < 3 minutes)**

```bash
# 1. clone
git clone https://github.com/<anonymized-during-review>/cooling-rag-multigranular.git
cd cooling-rag-multigranular

# 2. install
pip install -r requirements.txt

# 3. download data + LLM response cache from Zenodo
wget https://zenodo.org/record/<ZENODO_RECORD>/files/cooling_rag_data.tar.gz
tar -xzf cooling_rag_data.tar.gz

# 4. reproduce one requirement (cached, deterministic)
jupyter notebook notebooks/quickstart.ipynb
```

**Full reproduction (rerun the LLM)**

```bash
# requires DEEPSEEK_API_KEY in .env
python scripts/26_run_three_rounds.py --groups G1 G2 G3 G4 A1 A2
python scripts/22_compute_metrics.py
python scripts/27_statistics.py     # per-requirement mixed-model + bootstrap CI
python scripts/28_baselines.py all  # external baselines (E-1, E-2, E-22, E-23, A3)
python scripts/29_analysis.py all   # depth analyses (E-5, E-9, E-10, E-13, E-14)
```

---

## 开发流程

独立的新工程。旧工程不需要改。

目标流程：

1. 从 `data/raw/evidence.docx` 解析原始证据条目。
2. 自动生成三层证据库。
   - `source_chunks.jsonl` 大颗粒度章节块。
   - `evidence_units.jsonl` 小颗粒度证据条目。
   - `evidence_groups.jsonl` 同组证据。
3. 分别为 source_chunks 和 evidence_units 建索引。
4. UI 收集利益相关方需求。
5. 对原始需求拆分子需求。
6. 先大颗粒度检索，再小颗粒度检索。
7. 组扩展，RRF 融合，去重，LLM 证据审查。
8. 保存干净证据包。

## 安装

```bash
pip install -r requirements.txt
```

## 第一次运行

```bash
# 构建 FAISS + BM25 索引（仅需一次）
python scripts/11_build_multigranular_indexes.py

# 启动 UI
streamlit run app.py
```

## DeepSeek

在 `.env` 中配置（参考 `.env.example`）：

```
DEEPSEEK_API_KEY=你的key
```

不配置 DeepSeek 也能运行，会使用规则拆分和本地重排。

## 输出

检索结果保存到：

```
data/search_results/batch_YYYYMMDD_HHMMSS/
  all_requirements_results.json
  all_requirements_results.md
```
