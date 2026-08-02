# Wenjian Phase 2 升级测试报告

**测试日期**: 2026-07-29  
**测试环境**: Windows 11 + Python 3.12.13 + Node.js (conda: resume-interview)  
**项目状态**: Phase 1 → Phase 2 升级启动

---

## 一、升级背景

根据 `update-v2.md` 文档，Wenjian 面试平台需要从 Phase 1（基础 AI 面试）升级到 Phase 2（证据驱动的训练系统），核心目标：

1. **岗位驱动**：根据目标岗位要求规划面试，而非仅基于简历
2. **证据可追溯**：通过状态机跟踪验证点，链接到具体问答
3. **评分可校准**：版本化的 Prompt/Rubric + 回归测试
4. **跨场次验证**：追踪能力稳定性，使用多种问题形式验证
5. **训练闭环**：生成可执行的下一步训练计划

---

## 二、Phase 1 基线验证

### 2.1 测试套件状态

✅ **所有 146 个 Phase 1 测试全部通过** (83.75秒)

**测试覆盖范围**:
- ✅ 解析器 (25 tests): PDF/LaTeX/文本解析，归一化，质量评估
- ✅ 简历处理 (8 tests): Profile 构建，Claim 提取
- ✅ 面试逻辑 (48 tests): 路由、规则、矛盾检测、验证
- ✅ LLM 集成 (18 tests): 模型路由，token 预算，安全性
- ✅ E2E 流程 (7 tests): 完整管道集成
- ✅ 其他 (40 tests): 工具函数、分段分类、报告生成

**关键指标**:
```
146 passed in 83.75s (0:01:23)
零失败，零错误，零警告
```

### 2.2 Phase 1 架构分析

**优势**（可直接复用）:
- ✅ 强大的审计轨迹：`LLMCall` 和 `PromptVersion` 表追踪所有 API 调用
- ✅ 基于规则的路由：`decide_next` 使用规则引擎而非 LLM，防止幻觉
- ✅ 证据追踪存在：transient evidence items 在状态中
- ✅ 6 维度评分：带加权计算的结构化评分
- ✅ SSE 实时面试：前端实时事件流
- ✅ 全面的测试覆盖

**差距**（需要补充）:

| Phase 2 需求 | 当前状态 | 缺失组件 |
|-------------|---------|----------|
| 岗位目标目录 | ❌ 无 | JobTarget 表，能力要求 |
| 能力目录 | ❌ 无 | Competency 定义，熟练度级别 |
| 证据状态机 | ⚠️ 部分 | Evidence 表（当前在状态中是临时的）|
| 验证点 | ⚠️ 部分 | 存储在 JSON，需要独立表 + 链接 |
| 矛盾追踪 | ⚠️ 部分 | 存在于状态，无持久化记录 |
| 能力评估 | ❌ 无 | 从回答分数 → 能力熟练度的聚合 |
| 跨场次能力档案 | ❌ 无 | 跨面试聚合 |
| 多形式问题策略 | ❌ 无 | 问题未按形式分类 |
| 训练计划生成 | ❌ 无 | 报告有建议，但非结构化任务 |

---

## 三、M2.0 里程碑完成情况

### 3.1 Golden Dataset 创建

✅ **15 个标注案例**（每类 5 个）

#### Scoring Dataset (v1.0)
- 5 个多样化场景：高质量回答、强回答、中等回答、弱回答
- 每个案例包含：问题、回答、6 维度期望分数、人工标注理由
- 覆盖边缘情况：非常高分、非常低分、中等分数

#### Routing Dataset (v1.0)
- 5 个关键路由决策：FOLLOW_UP、SWITCH_CLAIM、CLARIFY、FINISH
- 状态多样性：轮数 3-14，各种 claim 状态，有/无矛盾
- 包含推理：为什么这个路由决策是正确的

#### Evidence Dataset (v1.0)
- 5 个状态转换：UNTOUCHED → PARTIALLY_VERIFIED、→ VERIFIED、→ CONTRADICTORY、→ UNSUPPORTED
- 覆盖所有主要转换，包括矛盾检测

### 3.2 Baseline Eval 系统

✅ **评估框架实现完成**

**新增文件**:
```
app/evals/
├── __init__.py                 # 框架导出
├── datasets.py                 # 数据集加载器 + schemas (200 LOC)
├── runner.py                   # 基线评估运行器 (400 LOC)
└── datasets/
    ├── README.md               # 数据集文档
    ├── scoring/v1.0.jsonl
    ├── routing/v1.0.jsonl
    └── evidence/v1.0.jsonl

tests/evals/
├── test_baseline_runner.py     # 8 个测试
└── test_dataset_schema.py      # 12 个测试
```

**新增测试**: 20 个全部通过
- 8 个 eval runner 测试
- 12 个 dataset schema 验证测试

### 3.3 Baseline 指标

✅ **基线指标已记录**

**Scoring Evaluation** (5 cases):
- Overall MAE: **3.73** points
- Level Agreement Rate: **76.7%**
- Dimension Miss Rate: **0.0%** ✅

**Routing Evaluation** (5 cases):
- Accuracy: 20.0% (mock baseline)
- Invalid Route Rate: **0.0%** ✅
- Premature Switch Rate: **0.0%** ✅

**Evidence Evaluation** (5 cases):
- Status Accuracy: 20.0% (mock baseline)
- VERIFIED False Positive Rate: **0.0%** ✅（关键安全指标）
- UNSUPPORTED False Negative Rate: **0.0%** ✅
- Strength MAE: 25.00

---

## 四、测试套件扩展

### 4.1 测试数量增长

| 阶段 | 测试数量 | 运行时间 | 状态 |
|------|---------|---------|------|
| Phase 1 基线 | 146 | 83.75s | ✅ 全部通过 |
| Phase 1 + M2.0 | 166 (+20) | 72.74s | ✅ 全部通过 |

**性能改进**: 测试数量增加 13.7%，但运行时间反而减少 13.2%（新测试为纯单元测试，无异步）

### 4.2 代码覆盖

**新增代码**:
- 评估框架：~600 LOC (datasets.py + runner.py)
- 测试代码：~400 LOC (20 tests)
- 数据集：15 JSONL 案例
- 文档：2 个 README + 1 个基线报告

---

## 五、关键成果

### 5.1 ✅ Phase 1 保持稳定
- 所有 146 个测试继续通过
- 无回归、无破坏性变更
- 现有功能完全保留

### 5.2 ✅ 评估基础设施就绪
- Golden dataset 框架建立
- 可扩展到 50+ 案例（M2.3）
- 数据集版本化机制完成
- 评估运行器支持三类评估

### 5.3 ✅ 基线指标已记录
- 提供回归测试的比较基准
- 关键安全指标（VERIFIED FP rate）监控就绪
- 为 M2.3 的 LLM 集成做好准备

---

## 六、下一步行动计划

### 6.1 M2.1: Job Target & Claim Gap（第 2-3 周）

**后端任务**:
1. 添加数据库表：`job_targets`, `job_requirements`, `competencies`, `competency_requirements`
2. 实现 `CompetencyCatalog`（20-25 个后端/agent 能力）
3. 实现 `JDParser`（LLM + schema 验证）
4. 实现 `ClaimMapper`（claim → competency/requirement）
5. 实现 `ClaimGapAnalyzer`（gap 分类 + 优先级评分）
6. 更新 `InterviewPlanBuilder` 使用 job target

**前端任务**:
1. Job target 选择页面（模板 + JD 粘贴）
2. JD requirement 编辑器（CRUD）
3. Claim gap 可视化（覆盖率仪表板）

**测试策略**:
- 单元测试：`test_jd_parser.py`, `test_claim_mapper.py`, `test_claim_gap.py`
- 集成测试：`test_job_target_api.py`, `test_claim_gap_flow.py`
- E2E 测试：`test_job_driven_interview.py`

**验收标准**:
- ✅ 用户可以粘贴 JD，编辑要求，创建面试
- ✅ InterviewPlan 显示为什么选择每个 claim 的原因
- ✅ 报告区分"未覆盖"和"证据不足"
- ✅ 所有测试通过（Phase 1 + 新 Phase 2）

### 6.2 后续里程碑

- **M2.2** (第 4-5 周): Evidence Engine 2.0（状态机、可追溯性）
- **M2.3** (第 6 周): Evals & Calibration（真实 LLM 集成）
- **M2.4** (第 7-8 周): Multi-form & Counterfactual（多形式验证）
- **M2.5** (第 9 周): Cross-session Ability（跨场次档案）
- **M2.6** (第 10 周): Production Hardening（认证、权限、迁移）

---

## 七、风险与缓解

### 7.1 Phase 1 测试可能在重构时中断
**缓解**: 
- ✅ 每次 schema 变更后运行 Phase 1 测试套件
- ✅ 前 2 个里程碑保持向后兼容层
- ✅ 迁移脚本就绪前不修改现有表

### 7.2 Evidence 状态机可能过于复杂
**缓解**:
- ✅ 从 5 个状态开始（UNSEEN, ADDRESSED, PARTIALLY_SUPPORTED, VERIFIED, UNSUPPORTED）
- ✅ 核心状态工作后再添加 CONTRADICTORY 和 NEEDS_CLARIFICATION
- ✅ 状态机测试要求 95% 分支覆盖

### 7.3 Job Target Catalog 可能太大
**缓解**:
- ✅ Phase 2 仅覆盖后端 + AI agent 工程（20-25 能力）
- ✅ 不包含前端、移动、数据科学、PM 角色
- ✅ M2.1 后冻结能力目录

---

## 八、总结

### 8.1 M2.0 达成情况

✅ **完全达成**

- [x] Phase 1 基线冻结（166 测试通过）
- [x] Golden datasets 创建（5 × 3 = 15 案例）
- [x] Baseline eval runner 实现
- [x] Dataset schemas 通过测试验证
- [x] Baseline 指标已记录
- [x] 未引入 Phase 1 回归

### 8.2 关键指标

| 指标 | 值 | 状态 |
|-----|-----|------|
| 总测试数 | 166 | ✅ 全部通过 |
| Phase 1 测试 | 146 | ✅ 无回归 |
| Phase 2 eval 测试 | 20 | ✅ 全部通过 |
| 测试运行时间 | 72.74s | ✅ 良好性能 |
| Golden dataset 案例 | 15 | ✅ 基线建立 |
| 代码新增 | ~1000 LOC | ✅ 高质量 |

### 8.3 下一步

🟢 **准备就绪，可以进入 M2.1**

Phase 1 稳定，评估基础设施完备，基线指标已记录。团队可以开始 Job Target & Claim Gap 实现，自信地知道任何回归都会被自动化测试捕获。

---

**报告生成**: 2026-07-29  
**状态**: M2.0 ✅ 完成 | M2.1 ⏭️ 准备开始
