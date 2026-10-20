# 改造任务：EA 需求图导出脚本（`scripts/92_export_ea_native_xmi.py`）

## 背景与问题
脚本把 RAG 结果导出为 EA 原生 XMI 1.1，由作者在 Enterprise Architect 中导入并审核。现有版本存在以下问题：
1. SysML 需求的 `text` 属性（顶层 `<UML:TaggedValue tag="text" value="&lt;memo&gt;#NOTES#...">`）里塞进了 shall、判据、分级、派生类型、路由、验证方式、引用等全部内容，而且用 `wrap_cn()` 每 34 个字符插入一个换行。块上显示一大段碎文本，属性表里也难以阅读。
2. 元素 notes（`documentation`，即 `er_notes()` 的输出）与 `text` 内容基本重复。
3. 块尺寸硬设为 300×200，需求一多，整张图就无法查看。

**参照**：EA 自己导出的样例 `D:\cooling_rag_multigranular\XML\XML_of_EA\reqFig.xml`：
- 名称形如 `REQ-300 Temperature Control`；
- `id` 标签只放编号；
- `text` 标签只放**一句 shall，一整段，没有换行**；
- 没有 `documentation` 标签；
- 块尺寸约 110×170。

## 目标
块上只显示"编号 + 短标题 + 一句 shall"。其余信息作为**独立的 Tagged Values**（EA 中元素属性的 Tags 页签），一个字段一个标签，便于逐项审核和筛选。

## 改动要求（必须遵守 TDD：先写测试、确认失败，再改代码）

1. **名称**：`"{OR编号}.{k} {英文短标题}"`，标题不超过 6 个英文单词，不含数字、单位和占位符（沿用 `gen_titles` 的规则）。源需求的格式为 `"{OR编号} {英文短标题}"`。
2. **`id` 标签**：只放编号，例如 `OR008.1`；源需求放 `OR008`。
3. **`text` 标签**：只放这条 shall 的**英文译文**，一整段。**禁止插入任何 `\n`**，去掉对 `wrap_cn` 的调用。源需求放原始需求的英文译文，不要再加 `[Source requirement]` 前缀。
4. **新增独立的 Tagged Values**，格式与 `id`/`text` 一样，写成顶层的 `<UML:TaggedValue tag=".." xmi.id=".." value=".." modelElement="{元素id}"/>`。每个工程需求包含：
   - `criterion`：判据的英文译文。`{{TBD|...}}` 占位符原样保留，只翻译其中的中文。
   - `grade`：A / B / C / X
   - `derivation`：Direct / Synthesized / Derived / Deferred / Unsupported
   - `review_route`：路由代码
   - `route_reason`：路由原因
   - `verification`：验证方式
   - `evidence_ids`：以 `; ` 分隔的、**经 KB 校验的**单元 ID，使用 `valid_citation_ids(er["evidence_citations"], kb)`，不要用 `cite_ids` 的正则结果
   - `evidence_tiers`：与 `evidence_ids` 一一对应的 L1/L2/L3
   - `evidence_sources`：去重后的来源文档名，以 `; ` 分隔
   - `shall_zh`：中文原文 shall，供作者对照译文

   源需求只需要 `id`、`text`、`text_zh`、`stakeholder`。

   所有 value 都经过 `esc()` 转义，**不得包含换行**。
5. **notes（`documentation` 标签）**：工程需求只写一行 `Grade {grade} | {derivation} | {review_route} | {evidence_ids}`，作为悬停时的摘要；源需求留空。不再重复 shall 全文。删除 `er_notes()`，或改成上面这种单行格式。
6. **块尺寸与间距**：工程需求块 160×110，源需求块 200×110；`gapx=190`，`gapy=170`。`group_layout(per_row=...)` 保持不变，默认每行 4 个。保留按分级着色。
7. **翻译的稳定性与校验**：
   - 把 `gen_titles` 和 `translate_en` 的结果缓存到 `data/search_results/exp_v4/ea_translation_cache.json`，键为中文原文的 sha1，避免每次导出结果不同。
   - 新增校验：中文判据中出现的每个数字，都必须出现在英文判据中（用 `cooling_rag_mg.numeric_norm.extract_numbers` 比较）。不满足时，`criterion` 改用中文原文，并在 stdout 中列出这些条目。
8. **同时导出审核用的表格** `data/search_results/exp_v4/ea_review_{tag}.csv`（utf-8-sig 编码，每条需求一行），列依次为：`id, name, text_en, shall_zh, criterion, grade, derivation, review_route, route_reason, verification, evidence_ids, evidence_tiers, evidence_sources`。
9. **保持不变的部分**：每组源需求单独一个文件（`--sets ORxxx` 生成 `ea_native_ORxxx.xml`）、`--per-row` 参数、Nesting 关联、XMI 头尾结构、`$ea_xref_property` 构造方式。

## 测试（新增 `tests/test_ea_export_format.py`）
构造只含 1 个源需求、2 个工程需求的假数据，并 monkeypatch `gen_titles`、`translate_en`，不调用 API。把生成 XMI 字符串的逻辑抽成函数 `build_xmi(sets, kb, titles, tr, per_row) -> str`，测试断言：
- 每个 `tag="text"` 的 value 都不含 `&#xA;`（即没有换行），并且只包含 shall 的译文；
- 每个工程需求都有 `criterion`、`grade`、`derivation`、`review_route`、`evidence_ids`、`shall_zh` 标签；
- `documentation` 是单行，并且不包含 shall 的全文；
- `evidence_ids` 中不出现 KB 里不存在的 ID；
- 判据中数字不一致时会回退到中文；
- 块尺寸为 160×110。

保留现有的 `tests/test_ea_layout.py`，并确保它继续通过。

## 验收
1. `PY -m pytest -q tests -p no:cacheprovider --deselect tests/test_grounding.py::test_load_evidence_text_map` 全部通过（使用 `tmp_path` 的测试在本机会报 PermissionError，属于环境问题，需单独说明）。
2. 运行 `PY scripts/92_export_ea_native_xmi.py --sets OR052`，以及 OR041、OR008，生成 3 个 XMI 和 3 个 CSV。
3. 交给作者在 EA 中导入。块上应只显示名称和一句 text；双击元素，在 Tags 页签中能看到各项字段；整张图在默认缩放下能完整显示。
4. 提交到分支 `revision-se-4762284`，并在 ledger（`.superpowers/sdd/2026-10-14-se-minor-revision/progress.md`）末尾追加完成记录。

## 环境提示
- Python 通过 `cmd.exe /c "D:\cooling_rag_multigranular\cooling_rag_multigranular\run_py.bat ..."` 调用。
- 导出脚本会调用 DeepSeek API 生成标题和翻译。有了缓存之后，重复导出不应再调用 API。
