# cooling_rag_multigranular

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

```bat
D:\Users\yando\anaconda3\envs\LangGraph_env\python.exe -m pip install -r requirements.txt
```

## 第一次运行

```bat
python scripts/10_convert_docx_to_multigranular_jsonl.py
python scripts/11_build_multigranular_indexes.py
python scripts/12_run_requirement_ui.py
```

## DeepSeek

如果要启用 DeepSeek 拆分和证据审查，在 Windows 终端设置：

```bat
setx DEEPSEEK_API_KEY "你的key"
```

然后重启 PyCharm。

不配置 DeepSeek 也能运行，会使用规则拆分和本地重排。

## 输出

检索结果保存到：

```text
data/search_results/batch_YYYYMMDD_HHMMSS/
```

每个批次会生成：

```text
all_requirements_results.json
all_requirements_results.md
```
