# 论文证据强化设计 — 用最强方式支撑核心结论

**日期：** 2026-05-29
**状态：** 设计已确认，待写实施计划
**目标论文：** Multi-Granular RAG for Evidence-Based Engineering Requirement Formulation in Ship Cooling Systems（JMSE）

---

## 1. 背景与问题诊断

论文的原始命题是：**多粒度检索为 LLM 转换原始需求为工程需求提供更好的证据支撑，减轻 AI 幻觉**。但通读代码与实验数据后发现，这个命题在当前实验中**从未被正确测量过**，而非被证伪。

### 1.1 核心诊断：现有指标测的是"文本形式"，不是"证据质量"

- `quality_gate.py:251` `_over_inference`（M3）只检测：shall 里有无带单位数字 + `support_status` 标签。**完全不读证据内容。**
- `quality_gate.py:199` `_verifiability`（M4）只检测：`verification_method` 是否存在、`acceptance_criteria` 是否非空、有无模糊词。**全是生成文本的形式特征。**
- `experiment_runner.py:388,392` 的 M3/M4 直接调用上述两个函数。

**铁证：** G1（零检索证据）的 M3=4.12%，比 G2（有检索）的 4.49% 还低。若 M3 真测"证据抑制幻觉"，这在物理上不可能发生。说明幻觉抑制来自 `engineering_requirement_agent.py:68` 起的"数值安全规则"prompt + 460 行的正则二次清洗，**与检索证据无关**。

### 1.2 衍生问题

- **Profile Scoring 在 T=0 下隐形**：G3=G4 数值完全相同（T=0 + 缓存使 top-k 成员不变 → prompt 字节相同 → 输出相同）。
- **M6 只在 G4 单组做**：唯一能测证据质量的指标，从未做 G2 vs G3 vs G4 横向对比。
- **长上下文基线在 M1/M3 上优于本系统**：核心竞争力未经实验验证（KB 扩展/噪声实验当时未跑完）。
- **p=0.053 不显著**：核心声明统计功效不足。
- **测试需求由 DeepSeek 生成**：与评估同系模型，循环依赖。

### 1.3 归因结论

不是模型局限，主因是 **度量设计 + prompt 过强 + 评估协议（T=0）+ KB 规模** 四者叠加，使证据质量差异无法被现有自动指标捕捉。要支撑原始命题，必须**换尺子**（新增能穿透 prompt 的证据质量指标），并给 Profile Scoring 公平的检验条件（T>0）。

---

## 2. 目标与资源约束

### 2.1 目标（用户已确认：两者都做，效果优先于时间成本）

1. **检验原始命题**：用正确指标判定"多粒度→更好证据"成立或证伪。
2. **加固现有结论**：把审稿人能挂掉论文的硬伤全部堵上。

### 2.2 可用资源（用户已确认）

- ✅ API 预算 + 算力充足
- ✅ 可 API 的独立模型：**Qwen + 文心（ERNIE）**（均区别于生成所用的 DeepSeek，两个独立厂商）
- ✅ ChatGPT / Codex：**仅手动**（网页/交互，不能 API）→ 可选小样本人工复核 + Codex 辅助写代码
- ❌ 真人船舶/系统工程专家
- ❌ 真实船厂/船级社需求

### 2.3 天花板（无法根除，须作为保留 limitation 诚实写明）

- **R2-M2（真人专家验证）**：无真人 → 只能做"多模型一致性"，不能叫"专家验证"。
- **R2-M1（真实需求）**：无真实数据 → 第二 LLM 生成独立测试集只能**缓解**循环依赖，不能根除。

---

## 3. 动作设计（A–G）

### A. 证据-需求语义契合度指标（核心，grounding score）

**目的：** 给"证据质量"装上正确的尺子，穿透 prompt 约束，直接量化"被引证据多支持生成的 shall"，在 G2/G3/G4 横向对比，检验原始命题。

**计算对象：** 每条 `evidence_ids` 非空的 ER，取 `(shall_statement, 每条 evidence_id 原文)`。仅对有证据的 ER 计算，避免与 M1 混淆。

**两个互补测法（用户确认：都用）：**
1. **Reranker 客观分**：用现成 BGE-reranker 对每个 `(shall, evidence)` 对算相关性分。纯本地、零 API、完全可复现。
2. **LLM 蕴含分**：用 Qwen（独立于生成所用的 DeepSeek）对每个 `(shall, evidence)` 对判"支持/部分支持/不支持"→ 1/0.5/0。可选用文心（ERNIE）复算一遍作模型间一致性检查。

**聚合粒度（明确）：** 先算每个 `(shall, evidence)` 对的分；per-ER 分 = 该 ER 所有引用证据的**均值**（主指标，反映"平均支持度"），同时记录最大值作辅助稳健性检查。两个测法各产出一个 per-ER 分。

**检验：** per-ER grounding score 在 G2/G3/G4 上算分布（mean ± bootstrap CI），G2 vs G3 做 per-ER 配对 Wilcoxon。报告两个测法各自结果及其一致性（Spearman/Pearson）。

**判定逻辑：** 若多粒度真提供更对口证据，G3 grounding score 应显著 > G2。这是 M3/M4 测不到、grounding score 能测到的差异。

**新脚本：** `scripts/40_grounding_score.py`，读取已有 batch 的 G2/G3/G4 结果 + evidence KB，输出 `grounding_score.json` + LaTeX 表。

### B. M6 溯源精度横向对比

**目的：** 把 M6 从 G4 单组扩到 G2/G3，提供"溯源精度随粒度提升"的横向证据，作为 A 的人工对照。

**标注协议：** 第一作者 + Qwen 代理双标注，报 LLM-human 一致性（Cohen κ）。**表述天花板：称"多源一致性"，非"专家验证"。**

**范围：** G2/G3/G4 各 ~90 条 ER（三轮）的溯源精度。

### C. T>0 多轮重跑（增量，不推翻 T=0）

**设计：** 保留现有 T=0 三轮为确定性主结果。**新增 T=0.3 × 5 轮**，专门报告：
- Profile Scoring 在有随机性下是否显现（G3 vs G4，M1/M3/M4 + grounding score）
- 提升统计功效（更大 n）

**脚本：** 复用 `scripts/26_run_three_rounds.py`，新增 `--temperature 0.3 --seeds <5 seeds>` 运行。注意 T>0 缓存命中率下降，须预留 API 预算。

### D. 多 LLM 交叉验证

**设计：** 用 **Qwen 和文心（ERNIE）** 各重跑 G1–G4（3 轮），对比 DeepSeek 的结论**方向**是否一致（M1/M3/M4/grounding score 的组间排序是否稳定）。两个独立厂商模型，跨模型稳健性证据更强。

**目的：** 证明结论不是单一模型偏好，堵"单一后端"（R3-M3）。

### E. KB 扩展 + 噪声鲁棒性完整实验

**设计：** 已有 `data/indexes_scaling/`（200/500/1000/noise）。把当前单轮（seed 42）扩为 **3 seed** 跑，把论文里"anticipated"改成"demonstrated"。

**目的：** 提供"多粒度 vs 长上下文基线"竞争力的实验证据，堵 R1-M1。

### F. 质量门多 LLM 校准

**设计：** 质量门判决 vs **Qwen + 文心（ERNIE）** 两个独立 proxy（均可 API，全自动），报三方一致性（DeepSeek-QG / Qwen / 文心，Fleiss κ）。可选再用 ChatGPT 手动复核 30–50 条作第四方人工抽查。

**目的：** 部分堵 R2-M2。**表述天花板：称"多模型一致性校准"，非"专家验证"——三个独立厂商模型增强独立性，但仍非真人。**

### G. 第二 LLM 生成独立测试集

**设计：** 用 Qwen（或文心）生成 **100 条**独立需求（对标主池规模），G4 上跑，与 DeepSeek 主池结果对比。

**目的：** 部分破循环依赖，堵 R2-M1（缓解，非根除）。

---

## 4. 统计方法

- 主结论：per-ER 配对 Wilcoxon + bootstrap CI（沿用现有）。
- **新增功效分析**：达到 p<0.05 所需样本量（直接回应 R4-M1）。
- T=0.3 × 5 轮提升 n，给 grounding score 和 M4 更大功效。
- **多重比较校正**（Holm 或 BH）：指标增多，控制族错误率。

---

## 5. 叙事双分支（两套都预先准备）

- **分支甲（grounding score：G3 显著 > G2）→ 原始命题成立**：主线升级为"多粒度检索提供语义更契合的证据，进而提升可验证性"，A 指标成为核心证据。
- **分支乙（无显著差异）→ 原始命题证伪**：主线转为"当前 KB 规模下检索粒度对证据质量无显著影响；真正瓶颈是 KB 覆盖（94.8% 失效）"。A 指标的零结果本身是诚实的方法论贡献，配合"精度-覆盖权衡"定性描述。

两套都站得住。无论结果如何，A 让核心主张第一次有了正确的测量工具。

**决策留痕（2026-05-29）：** 用户在权衡后确认**接受双分支**——若 grounding score 证伪原始命题，论文走分支乙（KB 覆盖瓶颈的诊断性贡献），不通过"换战场/调参"强行证明多粒度优势，以守住学术诚信。动作 E（KB 扩展/噪声）定位为诚实的竞争力验证，报告真实结果，不预设多粒度一定胜出。

---

## 6. 审稿意见覆盖映射

| 动作 | 堵住的审稿意见 | 程度 |
|---|---|---|
| A | R1-M3（G3/G4 无法区分）、R4 | 根除 |
| B | R1-M2（IR 循环论证的替代品） | 大部分 |
| C | R4-M1（p=0.053、统计功效） | 根除 |
| D | R3-M3、单一后端 | 根除 |
| E | R1-M1（核心竞争力 vs 长上下文） | 根除 |
| F | R2-M2（专家验证）→ DeepSeek/Qwen/文心 三模型自动一致性 | 部分（无真人，天花板） |
| G | R2-M1（真实需求循环依赖） | 部分（天花板） |

**保留 limitation：** R2-M1（真实需求）、R2-M2（真人专家）无法根除，诚实写明。

---

## 7. 执行顺序与依赖

```
第一批（可并行，纯计算/已有数据）：
  A  grounding score  ← 读现有 T=0 batch 的 G2/G3/G4
  E  KB扩展/噪声 3seed ← 已有 indexes_scaling
  B  M6横向对比标注   ← 现有 G2/G3/G4 ER

第二批（API 密集，依赖第一批的指标定义）：
  C  T>0 × 5轮重跑    → 产出新 batch，再跑 A 的 grounding score
  D  Qwen 跨模型重跑  → 同上
  G  Qwen 独立测试集

第三批（依赖前两批产出）：
  F  质量门多LLM校准（DeepSeek/Qwen/文心）
  统计：功效分析 + 多重比较校正
  叙事分支选定 + 论文章节改写
```

**关键路径：** A 是核心，且第一批就能用现有数据出结果——它最早能告诉我们原始命题成立与否，从而决定后续叙事分支。建议 A 优先。

---

## 8. 新增/修改文件清单

| 文件 | 动作 | 说明 |
|---|---|---|
| `scripts/40_grounding_score.py` | 新增 | A：grounding score 计算 + LaTeX |
| `scripts/41_cross_model.py` | 新增 | D：Qwen + 文心 跨模型重跑封装 |
| `scripts/42_qg_calibration_multi.py` | 新增 | F：多 LLM 质量门校准（DeepSeek/Qwen/文心）+ Fleiss κ |
| `scripts/26_run_three_rounds.py` | 修改 | C：支持 `--temperature` 参数 |
| `scripts/28_baselines.py` | 修改 | E：KB 扩展/噪声支持多 seed |
| `scripts/25_generate_requirement_pool.py` | 参考 | G：用 Qwen 后端生成独立池 |
| `scripts/27_statistics.py` | 修改 | 功效分析 + 多重比较校正 |
| `cooling_rag_mg/config.py` | 修改 | 新增 Qwen + 文心后端配置 |
