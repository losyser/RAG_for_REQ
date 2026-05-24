# V2 部件化证据库代码修改说明

本补丁适配 `evidence_component_structured_v2.docx`。

## 核心变化

1. `docx_parser.py`
   - 支持 `E-SYS-ACCESS-001` 这类语义化证据编号。
   - 支持 V2 字段：部件对象、需求方面、工程阶段、适用工况、可支撑类型、证据强度、是否可泛化、适用性等级、不能支撑的需求等。
   - 正确保留原文、整理说明、可支撑需求和不能支撑需求。

2. `schema.py`
   - 新增 `normalize_v2_metadata()`。
   - 统一 V2 字段和旧字段。

3. `granularity_builder.py`
   - 将 V2 元数据写入 `search_text`。
   - source chunk 和 evidence group 改为按部件、需求方面和工程阶段聚合。

4. `retrieval_profile.py`
   - 从需求中识别目标部件、需求方面、工程阶段、适用工况和可支撑类型。

5. `retrieval_engine.py`
   - 检索排序从“文本相似度优先”改为“工程字段匹配优先”。
   - 加入 component、aspect、can_support、phase、condition、evidence_strength、applicability_level 权重。

6. `applicability_filter.py`
   - 使用 V2 的证据强度、适用性边界、不能支撑项进行过滤。

7. `evidence_judge.py`
   - LLM 证据审查时强制检查 V2 元数据。

8. `pipeline.py`
   - background 证据不再解除 evidence gap。
   - evidence gap 细分为参数、施工、验证、控制报警等缺口类型。

9. `engineering_requirement_agent.py`
   - 工程化需求生成只基于原始需求和 direct/indirect 证据。
   - 子需求只作为检索中间产物，不再作为最终生成依据。
   - 增加 JSON 修复和更保守的 fallback。

## 使用方式

把 `cooling_rag_mg`、`scripts`、`apps` 覆盖到你的项目根目录。

然后确认 V2 文件放到：

```text
D:\cooling_rag_multigranular\cooling_rag_multigranular\data\raw\evidence_component_structured_v2.docx
```

或者在 `.env` 里设置：

```text
RAW_DOCX_PATH=D:/你的路径/evidence_component_structured_v2.docx
```

重建数据和索引：

```bat
conda activate cooling_rag_env
cd /d D:\cooling_rag_multigranular\cooling_rag_multigranular
python scripts\10_convert_docx_to_multigranular_jsonl.py
python scripts\11_build_multigranular_indexes.py
python scripts\12_run_requirement_ui.py
```
