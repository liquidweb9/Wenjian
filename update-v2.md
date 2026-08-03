# Wenjian 第二阶段核心差异化开发文档

> 文档用途：第二阶段产品设计、研发评审、任务拆解、测试设计与小范围公测验收  
> 适用项目：`liquidweb9/Wenjian`  
> 文档版本：v2.0  
> 阶段定位：从“能完成一次动态 AI 面试”升级为“能围绕目标岗位验证简历 Claim、保留证据链，并通过多场面试检验能力迁移的面试训练系统”  
> 核心原则：第二阶段优先建设 P0、P1 差异化能力，不扩展复杂 RAG、实时语音、视频分析、在线 IDE 或大而全求职平台。

---

## 1. 文档调整说明

原第二阶段文档以“全面生产化”为主线，将账号体系、异步 Worker、多实例事件、管理后台、完整可观测性、岗位能力模型、Evidence、Evals 和成长闭环同时纳入，范围过大，容易出现以下问题：

1. 基础设施投入过多，核心产品差异迟迟无法被用户感知；
2. 岗位能力模型、Claim Gap、Evidence 和跨场次复验被排在后期；
3. 第二阶段结束后可能得到一个更稳定的系统，却没有形成明显区别于普通 AI 模拟面试项目的核心能力；
4. 单人或小团队同时建设完整 Worker、Redis Event Bus、管理后台、语音、RAG、企业权限体系，开发与维护成本过高。

因此，本版将第二阶段重构为两条主线：

```text
主线 A：可信验证
目标岗位 → Claim Gap → Verification Point → Evidence 状态 → 可追溯报告

主线 B：训练闭环
首次面试 → 弱点识别 → 多形式复验 → 反事实问题 → 跨场次能力变化
```

基础设施只建设支撑上述两条主线所必需的最小集合。

---

## 2. 第二阶段核心目标

第二阶段不以题目数量、模型数量或交互形式作为主要指标，而以以下五项能力为核心。

### 2.1 岗位驱动，而不只是简历驱动

系统不仅知道“候选人写了什么”，还要知道：

- 目标岗位要求什么；
- 哪些简历 Claim 与岗位高度相关；
- 哪些关键岗位能力没有被简历覆盖；
- 哪些 Claim 虽然相关，但证据强度不足；
- 当前面试为什么优先验证某个 Claim 或能力。

### 2.2 Evidence 可追溯，而不只是给分

系统需要把“评分结果”升级为“可解释判断”：

```text
Claim：我设计了 Redis 缓存方案
状态：PARTIALLY_SUPPORTED

已支持：
- 能说明 Cache Aside 基本流程
- 能说明缓存 Key 组成

仍缺失：
- 一致性处理
- 命中率数据来源
- 本人主导证据

状态依据：
- Question Q3
- Answer A3 的第 2、4 段
- Evidence Policy v2.1
```

### 2.3 评分可校准，而不是依赖一次 LLM 判断

第二阶段必须建立最小可用的人工标注样本、Prompt 版本和回归测试，使评分与路由修改可以被比较。

### 2.4 跨场次验证，而不只是保存历史分数

系统需要判断用户是否真正掌握能力，而不是只判断“第二次说得更像参考答案”。同一能力应通过不同问题形式验证：

- 直接解释；
- 项目实现；
- 故障排查；
- 反事实变化；
- 架构权衡。

### 2.5 给出下一轮训练动作，而不只输出总结

最终报告应明确回答：

1. 哪些 Claim 已被支持；
2. 哪些 Claim 仍缺证据；
3. 哪些能力是目标岗位要求但尚未覆盖；
4. 下一次面试应重新验证什么；
5. 用户应该完成什么具体训练任务。

---

## 3. 第一阶段基线

当前系统已具备以下闭环：

```text
简历上传
  → 文本解析
  → 用户确认
  → Profile 构建
  → Claim 抽取
  → InterviewPlan
  → 动态提问
  → 回答分析
  → 六维评分
  → Evidence 更新
  → Coaching
  → 路由决策
  → 最终报告
```

第二阶段应继续保留以下已有设计：

- Profile、Claim、Question、Answer、Evaluation、Report 持久化；
- 关键路由由代码策略控制；
- LLM 负责结构化分析、生成候选内容和辅助 Judge；
- Checkpoint、数据库恢复、SSE 快照和重复提交控制；
- 前端 Dashboard、Resume、Interview、Report、Analytics 主流程。

第二阶段原则上不重写现有 Agent Graph，而是在现有节点前后增加目标岗位、证据策略、跨场次记忆和训练闭环。

---

## 4. 第二阶段范围与优先级

## 4.1 P0：必须完成的核心差异化能力

### P0-1 目标岗位与 JD 结构化

- 用户可选择内置岗位模板；
- 用户可粘贴 JD；
- 系统把 JD 解析为结构化 JobRequirement；
- 用户可人工编辑解析结果；
- 不使用向量数据库，不建设复杂 RAG；
- JD 只作为当前面试的结构化输入。

### P0-2 Claim—岗位要求映射与 Gap 分析

- Claim 映射到 Competency 和 JobRequirement；
- 计算岗位相关度、证据强度和验证优先级；
- 区分“未覆盖”和“能力不足”；
- InterviewPlan 可解释每一个验证目标的来源。

### P0-3 Evidence Engine 2.0

- 为每个 Claim 拆分 Verification Point；
- Evidence 使用明确状态机；
- 每次状态变化保存证据片段与原因；
- 报告可追溯到具体问题和回答；
- 矛盾状态必须可澄清，不直接做诚信判断。

### P0-4 评分、路由和 Evidence 的 Eval 基线

- Prompt 版本化；
- Rubric 和 Policy 版本化；
- 建立第一版人工标注 Golden Dataset；
- 对评分、路由、Evidence 状态进行回归测试；
- 关键 Prompt 更新必须生成差异报告。

### P0-5 Evidence 与 Gap 的前端可视化

- Claim Passport；
- JD Coverage；
- Evidence Timeline；
- 未解决矛盾与待澄清项；
- 报告中的证据链接；
- 下一轮优先验证项。

### P0-6 最低生产基础

只建设支持 P0/P1 所必需的基础能力：

- 基础登录或现有身份机制；
- 用户数据归属和对象级权限；
- 提交回答幂等；
- 任务失败可恢复；
- Prompt、模型、Policy、Rubric 版本记录；
- 核心 E2E、错误码、日志脱敏；
- 简历、面试和报告基本删除能力。

## 4.2 P1：完成训练闭环的增强能力

### P1-1 跨场次能力档案

- 聚合多次面试中的能力证据；
- 同一能力按 Rubric 版本分别记录；
- 区分一次表现和稳定表现；
- 记录能力置信度、证据覆盖形式和最后验证时间。

### P1-2 多形式能力复验

同一能力至少支持以下验证方式：

```text
CONCEPT            概念解释
PROJECT_DETAIL     项目实现细节
DEBUGGING          故障排查
TRADEOFF           架构权衡
COUNTERFACTUAL     反事实变化
TRANSFER           新场景迁移
```

### P1-3 反事实面试

围绕用户已陈述的项目事实生成变化条件，例如：

- 流量扩大十倍；
- Redis 故障；
- 不允许使用消息队列；
- 成本必须下降一半；
- 数据一致性要求提高；
- 单体系统需要拆分；
- 重新设计时必须删除一个组件。

反事实问题用于验证理解和迁移能力，不用于故意刁难用户。

### P1-4 面试配置

用户创建面试时可选择：

- 目标岗位；
- 目标职级；
- 面试轮次；
- 面试重点；
- 是否优先复验历史弱点；
- 面试强度；
- 预计轮数。

### P1-5 下一轮训练计划

报告自动生成：

- 待补证据 Claim；
- 待覆盖岗位能力；
- 推荐复验方式；
- 具体训练任务；
- 任务完成标准；
- 下一场面试建议配置。

### P1-6 同题重答与回答对比

- 原回答不可覆盖；
- 新回答形成版本；
- 对比新增事实、减少歧义和评分变化；
- 判断用户是否只复述 Coaching；
- 需要时用不同题目重新验证同一能力。

---

## 5. 明确不纳入第二阶段

以下内容在第二阶段全部暂缓：

- 复杂面经 RAG；
- 向量数据库；
- 公司面经自动抓取；
- 实时语音面试；
- TTS、ASR 和语音情绪分析；
- 摄像头、表情、眼神或所谓诚信识别；
- 在线代码 IDE；
- 自动运行不可信代码；
- 多 Agent 自由协商；
- 招聘企业端候选人自动排名；
- 大型管理后台；
- 复杂组织权限；
- 求职岗位爬虫；
- 简历自动投递；
- 社区、课程和题库商城；
- 为追求“生产级”而提前引入不必要的微服务拆分。

第三阶段是否加入上述功能，应由真实用户数据决定，而不是在第二阶段预设。

---

## 6. 第二阶段目标用户流程

```text
1. 用户上传并确认简历
        ↓
2. 选择目标岗位、职级和面试轮次
        ↓
3. 选择岗位模板或粘贴 JD
        ↓
4. 系统生成可编辑 JobRequirement
        ↓
5. Claim 映射岗位能力并生成 Claim Gap
        ↓
6. InterviewPlan 按以下因素排序：
   岗位重要性 × Claim 风险 × 证据缺口 × 历史弱点
        ↓
7. 面试中持续更新 Evidence State
        ↓
8. 对关键能力使用不同形式复验
        ↓
9. 报告展示 Claim Passport、岗位覆盖和证据链
        ↓
10. 生成下一轮训练计划
        ↓
11. 下一场面试优先验证未解决问题
```

### 6.1 InterviewPlan 优先级建议

优先级由代码计算，不允许模型直接给出最终排序。

```text
priority_score =
    job_importance
  × evidence_gap
  × claim_risk
  × interview_round_weight
  × historical_weakness_weight
  × freshness_weight
```

建议所有输入归一化到 `[0, 1]`。具体权重在 Eval 数据上校准，不在业务代码中硬编码。

---

## 7. 总体架构调整

第二阶段继续采用单体 API + 数据库 + Agent Runtime 的结构，不强制拆分微服务。

```text
┌─────────────────────────────────────────────────────┐
│ React Frontend                                      │
│ Setup / Interview / Claim Passport / Training Plan │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼──────────────────────────────┐
│ API Layer                                           │
│ Resume / Job Target / Interview / Evidence / Report│
└───────────────┬───────────────────────┬─────────────┘
                │                       │
┌───────────────▼────────────┐  ┌───────▼─────────────┐
│ PostgreSQL                 │  │ Agent Runtime       │
│ Domain / Versions / Evals  │  │ LangGraph + LLM    │
└────────────────────────────┘  └─────────────────────┘
```

### 7.1 暂不强制引入的基础设施

- Redis Event Bus；
- Kafka；
- 独立 Eval 服务；
- 独立 Evidence 微服务；
- 多实例 SSE Replay；
- 完整 Admin Portal；
- 全链路 OpenTelemetry 平台。

当出现以下真实需求时再引入：

- 单进程任务可靠性无法满足公测；
- 需要多个 Worker 并行执行；
- SSE 在多实例环境发生事件丢失；
- 排队时间和失败任务已无法人工处理；
- 日活和并发量证明拆分收益高于维护成本。

### 7.2 必须保留的架构原则

1. LLM 输出必须经过 Schema 校验；
2. 关键状态由规则层决定；
3. 所有状态更新可追溯；
4. Prompt、Model、Rubric、Policy 均记录版本；
5. Report 不重新计算评分；
6. 旧面试结果不因新 Prompt 自动变化；
7. 跨场次比较必须明确评分版本；
8. 用户输入不得覆盖 System Prompt 或业务权限。

---

## 8. 推荐目录结构

```text
app/
├── api/v1/
│   ├── resumes.py
│   ├── job_targets.py
│   ├── interviews.py
│   ├── evidence.py
│   ├── abilities.py
│   ├── training_plans.py
│   └── evals.py
├── resume/
│   ├── parser.py
│   ├── profile_builder.py
│   ├── claim_extractor.py
│   └── source_mapping.py
├── job_target/
│   ├── templates.py
│   ├── jd_parser.py
│   ├── requirement_editor.py
│   └── schemas.py
├── competencies/
│   ├── catalog.py
│   ├── level_descriptors.py
│   ├── mapper.py
│   └── coverage.py
├── planning/
│   ├── claim_gap.py
│   ├── target_ranker.py
│   ├── interview_plan.py
│   └── reason_codes.py
├── interview/
│   ├── graph.py
│   ├── state.py
│   ├── nodes/
│   ├── routing/
│   ├── question_forms.py
│   └── counterfactual.py
├── evidence/
│   ├── engine.py
│   ├── state_machine.py
│   ├── policies.py
│   ├── contradiction.py
│   ├── spans.py
│   └── passport.py
├── scoring/
│   ├── rubric.py
│   ├── calculator.py
│   ├── confidence.py
│   └── calibration.py
├── abilities/
│   ├── observations.py
│   ├── profile.py
│   ├── stability.py
│   └── transfer.py
├── coaching/
│   ├── answer_diff.py
│   ├── task_generator.py
│   └── training_plan.py
├── evals/
│   ├── datasets.py
│   ├── runner.py
│   ├── metrics.py
│   ├── regression.py
│   └── reports.py
└── versioning/
    ├── prompts.py
    ├── policies.py
    └── rubrics.py

frontend-react/src/features/
├── job-target/
├── interview-setup/
├── claim-gap/
├── interview/
├── claim-passport/
├── ability-profile/
├── training-plan/
└── eval-debug/

evals/
├── datasets/
├── annotations/
├── baselines/
└── reports/
```

---

# 9. P0 模块详细设计

## 9.1 目标岗位与 JD 结构化模块

### 9.1.1 目标

将用户提供的岗位信息转成可编辑、可计算、可追溯的结构化要求，而不是直接把整段 JD 反复塞进 Prompt。

### 9.1.2 输入方式

支持两种方式：

#### 方式 A：内置岗位模板

第一版建议只维护少量模板：

- Java 后端工程师；
- Go 后端工程师；
- Python 后端工程师；
- AI Agent 应用开发工程师；
- RAG 应用工程师；
- 通用后端实习生。

模板不是题库，只定义能力维度、职级描述和默认权重。

#### 方式 B：粘贴 JD

LLM 将 JD 解析为结构化要求，用户必须可在开始面试前修改。

### 9.1.3 核心数据结构

```text
job_targets
- id uuid pk
- user_id uuid
- title text
- company_name text nullable
- level intern | junior | mid | senior | staff | custom
- interview_round resume | project | technical | system_design | hr | custom
- source template | pasted_jd | manual
- raw_jd text nullable
- parser_prompt_version text nullable
- created_at timestamptz

job_requirements
- id uuid pk
- job_target_id uuid fk
- competency_code text
- title text
- description text
- importance numeric
- expected_level int
- evidence_expectation jsonb
- source_span jsonb nullable
- is_user_confirmed boolean
- created_at timestamptz
```

### 9.1.4 输出示例

```json
{
  "competency_code": "backend.cache_consistency",
  "title": "缓存与一致性",
  "importance": 0.85,
  "expected_level": 3,
  "evidence_expectation": [
    "能够解释缓存模式",
    "能够分析一致性风险",
    "能够说明监控与故障处理"
  ],
  "source_span": {
    "text": "熟悉 Redis 缓存及高并发场景",
    "start": 118,
    "end": 136
  }
}
```

### 9.1.5 关键规则

- JD 中出现技术词，不代表用户实际使用过；
- JD Requirement 只能定义“需要验证什么”；
- 不能自动转成“候选人缺少该能力”；
- 用户未回答前统一标记为 `UNCOVERED`，而不是 `WEAK`；
- JD 解析结果必须可编辑和删除；
- 不需要向量检索，普通结构化解析即可。

### 9.1.6 验收标准

- 用户可在创建面试时选择模板或粘贴 JD；
- 解析结果可人工修改；
- 每条 Requirement 可追溯到模板或 JD 原文；
- 删除某条 Requirement 后不会继续生成对应问题；
- 对相同确认结果，Coverage 计算具有确定性。

---

## 9.2 Competency Catalog 与职级描述

### 9.2.1 目标

建立一个小而稳定的能力目录，为 JD、Claim、Question 和 Ability Profile 提供统一语义。

### 9.2.2 初始能力目录

建议第一版只覆盖后端和 Agent 工程：

```text
backend.language_runtime
backend.api_protocol
backend.database_modeling
backend.transaction_consistency
backend.cache
backend.message_queue
backend.concurrency
backend.observability
backend.failure_recovery
backend.security
backend.system_design
backend.testing
backend.delivery

agent.prompt_design
agent.structured_output
agent.workflow_orchestration
agent.state_management
agent.tool_calling
agent.rag_fundamentals
agent.eval
agent.guardrail
agent.cost_latency
agent.production_reliability
```

### 9.2.3 职级描述

每个能力用行为描述区分等级，不直接用“初级、中级、高级”空泛打分。

示例：`backend.cache`

| 等级 | 可观察行为                         |
| ---- | ---------------------------------- |
| L1   | 能说明缓存的基本用途               |
| L2   | 能实现基本缓存读取与失效           |
| L3   | 能分析穿透、击穿、雪崩和一致性     |
| L4   | 能结合容量、监控、故障和成本做设计 |
| L5   | 能设计跨系统缓存治理和演进策略     |

### 9.2.4 验收标准

- 每个 Competency 都有稳定 code；
- 修改显示名称不会破坏历史记录；
- 每个等级都有可观察行为；
- Claim、Requirement 和 Question 均可映射到同一 Competency；
- 第二阶段不扩展到所有职业。

---

## 9.3 Claim—Requirement 映射与 Claim Gap

### 9.3.1 目标

回答三个问题：

1. 哪些 Claim 对目标岗位最重要；
2. 哪些岗位要求有简历 Claim 支撑；
3. 哪些要求尚未被验证。

### 9.3.2 数据结构

```text
claim_competency_mappings
- id uuid pk
- claim_id uuid fk
- competency_code text
- mapping_strength numeric
- mapping_reason text
- mapping_source rule | llm | user
- prompt_version text nullable
- user_confirmed boolean

claim_requirement_mappings
- id uuid pk
- claim_id uuid fk
- requirement_id uuid fk
- relevance numeric
- evidence_strength numeric
- verification_priority numeric
- reason_codes jsonb
- created_at timestamptz
```

### 9.3.3 Gap 分类

```text
SUPPORTED_CLAIM
简历存在相关 Claim，且已有较强证据。

HIGH_PRIORITY_WEAK_EVIDENCE
岗位高度相关，但 Claim 证据不足，应优先深挖。

UNCOVERED_REQUIREMENT
岗位需要，但简历和当前面试尚无证据。

LOW_RELEVANCE_CLAIM
简历中存在，但与当前岗位关系较弱。

CONTRADICTORY_CLAIM
存在尚未解决的重要矛盾。
```

### 9.3.4 规划规则

InterviewPlan 优先选择：

1. 高重要度 Requirement；
2. 高相关但 Evidence 较弱的 Claim；
3. 历史多次不稳定的能力；
4. 当前轮次需要的能力；
5. 尚未使用不同形式验证的关键能力。

### 9.3.5 Reason Code

每个 Target 必须保存至少一个可读原因：

```text
HIGH_JOB_IMPORTANCE
WEAK_EXISTING_EVIDENCE
RESUME_CLAIM_RISK
HISTORICAL_WEAKNESS
UNRESOLVED_CONTRADICTION
REQUIRES_TRANSFER_VALIDATION
INTERVIEW_ROUND_REQUIRED
```

### 9.3.6 验收标准

- 面试计划可以解释为什么选择某个 Claim；
- “JD 未覆盖”不会被错误展示为“用户不会”；
- Priority 由代码计算；
- 用户修改岗位要求后可重新生成计划；
- 计划更新不能修改已完成回答的历史归因。

---

## 9.4 Evidence Engine 2.0

### 9.4.1 目标

将 Evidence 从模型生成的描述升级为规则约束的状态机。

### 9.4.2 Evidence State

```text
UNSEEN
尚未触及。

ADDRESSED
回答涉及该点，但不足以判断。

NEEDS_CLARIFICATION
存在歧义，需要澄清。

PARTIALLY_SUPPORTED
已有相关证据，但关键细节不足。

VERIFIED
满足当前 Policy 的支持条件。

UNSUPPORTED
多轮验证后仍没有支持证据，或用户明确未参与。

CONTRADICTORY
关键陈述之间存在待解决冲突。
```

`VERIFIED` 只表示“在当前面试证据和当前 Policy 下得到支持”，不表示客观事实已经由外部材料证明。

### 9.4.3 Verification Point

每个 Claim 拆成多个可验证点。例如：

```text
Claim：主导设计了 Redis 缓存方案

VP1：本人承担的具体职责
VP2：缓存对象与 Key 设计
VP3：读写和失效流程
VP4：一致性处理
VP5：性能指标来源
VP6：异常、监控和恢复
```

### 9.4.4 状态转换原则

```text
UNSEEN → ADDRESSED
回答明确涉及该 Verification Point。

ADDRESSED → PARTIALLY_SUPPORTED
回答包含相关实现信息，但证据不完整。

PARTIALLY_SUPPORTED → VERIFIED
满足 Policy 阈值、有可定位证据、无未解决矛盾。

任意非终态 → NEEDS_CLARIFICATION
回答相关但歧义较大。

ADDRESSED/PARTIALLY_SUPPORTED → UNSUPPORTED
用户明确未参与，或在限定追问次数内仍无法提供支持。

任意支持态 → CONTRADICTORY
发现两条不可同时成立的重要陈述，等待澄清。
```

### 9.4.5 数据结构

```text
verification_points
- id uuid pk
- claim_id uuid fk
- competency_code text nullable
- description text
- point_type responsibility | implementation | metric | tradeoff | failure | other
- policy_version text
- created_at timestamptz

verification_point_states
- id uuid pk
- verification_point_id uuid fk
- interview_id uuid fk
- state text
- strength numeric
- confidence numeric
- unresolved_reason_codes jsonb
- updated_at timestamptz

 evidence_transitions
- id uuid pk
- verification_point_id uuid fk
- interview_id uuid fk
- from_state text
- to_state text
- reason_code text
- answer_id uuid nullable
- evaluation_id uuid nullable
- evidence_spans jsonb
- policy_version text
- prompt_version text
- model_name text
- created_at timestamptz
```

### 9.4.6 Evidence Span

Evidence Span 必须能定位到回答内容：

```json
{
  "answer_id": "uuid",
  "start": 42,
  "end": 128,
  "quote_hash": "sha256:...",
  "summary": "说明了缓存 Key 由 tenant_id 与 order_id 构成"
}
```

前端默认展示摘要，用户点击后定位原回答。

### 9.4.7 矛盾处理

发现潜在矛盾时：

1. 先标记 `NEEDS_CLARIFICATION` 或候选矛盾；
2. 生成针对性澄清问题；
3. 只有在独立 Judge 或明确规则确认后，进入 `CONTRADICTORY`；
4. 报告描述“回答之间存在未解决冲突”，不描述“候选人撒谎”；
5. 用户澄清后可回到 `PARTIALLY_SUPPORTED` 或 `VERIFIED`。

### 9.4.8 验收标准

- 每次状态变化都有 Transition；
- `VERIFIED` 必须有 Evidence Span；
- 状态机不直接采用模型返回的最终状态；
- 所有状态都有可达和可退出路径；
- 矛盾可以通过后续回答解决；
- 报告可以从 Claim 定位到 Question、Answer、Transition。

---

## 9.5 Claim Passport 与 Evidence 可视化

### 9.5.1 Claim Passport

每个 Claim 使用独立卡片展示：

```text
Claim：我负责消息消费重试机制
岗位相关度：高
当前状态：PARTIALLY_SUPPORTED
置信度：中

已支持
- 能说明指数退避
- 能说明最大重试次数

仍缺失
- 幂等处理
- 死信队列恢复
- 监控指标

待澄清
- “由我设计”与“基于团队公共组件”之间的职责边界

证据来源
- Q2 / A2
- Q4 / A4

下一轮建议
- 使用故障排查题复验
```

### 9.5.2 JD Coverage

报告中把岗位要求分为：

- 已有稳定证据；
- 已有部分证据；
- 尚未覆盖；
- 存在冲突；
- 本次不在面试范围。

不得把“尚未覆盖”计为零分。

### 9.5.3 Evidence Timeline

按时间展示：

```text
UNSEEN
  → ADDRESSED（Q2/A2）
  → PARTIALLY_SUPPORTED（Q4/A4）
  → NEEDS_CLARIFICATION（Q5/A5）
  → VERIFIED（Q6/A6）
```

### 9.5.4 验收标准

- 报告中每个状态可点击查看依据；
- 用户能区分分数、状态和置信度；
- 未覆盖不显示为失败；
- 旧报告保持原 Evidence Policy 版本；
- 前端不只展示雷达图和总分。

---

## 9.6 评分、路由和 Evidence Evals

### 9.6.1 目标

建立能阻止明显退化的最小 Eval 系统，而不是搭建大型评测平台。

### 9.6.2 第一版数据集

建议至少包含：

```text
scoring_golden
人工标注六维分数区间与关键理由。

routing_golden
给定状态后期望 CLARIFY、DEEPEN、SWITCH、COUNTERFACTUAL 或 END。

evidence_golden
给定 Verification Point 和回答后期望 Evidence State。

contradiction_golden
标注真正矛盾、可兼容陈述和信息不足。

question_contract
检查问题相关性、单问题约束、重复问题和深度层级。
```

### 9.6.3 Prompt 版本

```text
prompt_versions
- id uuid pk
- prompt_key text
- version text
- content text
- schema_version text
- status draft | active | retired
- created_at timestamptz
- metadata jsonb
```

每次 Evaluation 至少记录：

- model_name；
- prompt_key；
- prompt_version；
- rubric_version；
- evidence_policy_version；
- route_policy_version；
- latency；
- token usage。

### 9.6.4 指标

| 模块          | 初始指标                                        |
| ------------- | ----------------------------------------------- |
| Scoring       | 与人工分数 MAE、等级一致率、维度漏判率          |
| Routing       | 路由准确率、过早切换率、无效澄清率              |
| Evidence      | 状态准确率、VERIFIED 误判率、UNSUPPORTED 误判率 |
| Contradiction | Precision、Recall、澄清后纠正率                 |
| Question      | Claim 相关度、重复率、一次只问一个问题比例      |

指标阈值应根据首版数据集设定基线。第二阶段不先写死“必须达到行业标准”，而是要求新版本不能无解释地显著退化。

### 9.6.5 Eval Gate

生产 Prompt 激活前必须满足：

1. Schema Contract 全部通过；
2. 关键安全样本无阻塞性失败；
3. VERIFIED 误判率不高于基线容忍范围；
4. 路由没有明显增加死循环；
5. 生成当前版本与基线版本的差异报告。

### 9.6.6 验收标准

- 每个生产 Prompt 有版本；
- 可以重跑固定 Eval Case；
- 可比较新旧版本；
- 旧面试可追溯实际版本；
- Eval 失败能阻止 Prompt 激活；
- 数据集不直接使用未经授权的真实用户隐私。

---

# 10. P1 模块详细设计

## 10.1 跨场次 Ability Profile

### 10.1.1 目标

从“保存历史面试分数”升级为“记录能力被哪些形式验证、是否稳定、是否能迁移”。

### 10.1.2 数据结构

```text
ability_observations
- id uuid pk
- user_id uuid
- interview_id uuid
- competency_code text
- question_form text
- score numeric nullable
- evidence_state text
- confidence numeric
- rubric_version text
- evidence_policy_version text
- observed_at timestamptz

ability_profiles
- id uuid pk
- user_id uuid
- competency_code text
- current_level numeric nullable
- stability low | medium | high
- transfer_status untested | partial | demonstrated
- evidence_form_count int
- last_verified_at timestamptz nullable
- unresolved_gaps jsonb
- updated_at timestamptz
```

### 10.1.3 聚合规则

Ability Profile 不直接取最近一次分数，也不简单取平均值。

建议综合：

- 最近表现；
- 不同问题形式数量；
- Evidence State；
- 评分置信度；
- 是否跨场景复现；
- 是否存在未解决矛盾；
- Rubric 版本是否一致。

### 10.1.4 稳定性定义

```text
LOW
只有一次或单一形式证据。

MEDIUM
至少两次有效观察，或两种不同问题形式表现一致。

HIGH
多场次、多形式、包含迁移或反事实验证，且无重大冲突。
```

### 10.1.5 验收标准

- 历史能力不只展示分数折线；
- Rubric 不同的结果不会直接混算；
- 稳定性有确定性规则；
- 用户可以查看能力由哪些面试支持；
- 单次高分不会直接变成高稳定性。

---

## 10.2 Question Form 与多形式复验

### 10.2.1 Question Form

```text
CONCEPT
解释概念和基本机制。

PROJECT_DETAIL
说明真实项目实现。

DEBUGGING
根据故障现象排查。

TRADEOFF
比较方案与边界。

COUNTERFACTUAL
改变约束后重新设计。

TRANSFER
迁移到未见过的新场景。
```

### 10.2.2 选择策略

当一个能力已通过 `PROJECT_DETAIL` 初步支持时，不应连续生成同类改写问题，而应优先选择未覆盖形式。

```text
if evidence_state == VERIFIED
and question_form_count == 1
and competency_importance is high:
    choose TRADEOFF or COUNTERFACTUAL
```

### 10.2.3 重复问题检测

重复检测不需要向量数据库，可使用组合策略：

- Question Intent 枚举；
- Verification Point ID；
- Question Form；
- 关键词重合；
- 小模型或当前模型做二分类 Judge；
- 最近问题规则缓存。

### 10.2.4 验收标准

- 每个问题记录 Question Form；
- 同一 Verification Point 不连续生成同类问题；
- 高优先级能力至少可配置多形式复验；
- 路由能解释为什么选择该形式；
- 重复问题率纳入 Eval。

---

## 10.3 Counterfactual Interview

### 10.3.1 目标

通过改变约束检验用户是否理解原方案，而不是测试其是否背熟固定回答。

### 10.3.2 反事实来源

反事实必须基于已确认的项目上下文生成：

```text
原始事实：使用 Redis 缓存订单查询
变化条件：Redis 集群短时不可用
验证目标：降级、超时、回源保护和监控
```

### 10.3.3 反事实模板

```text
SCALE_CHANGE
流量、数据量或团队规模变化。

DEPENDENCY_FAILURE
数据库、缓存、队列或外部服务故障。

CONSTRAINT_REMOVAL
禁止使用原有组件。

COST_CONSTRAINT
成本或资源被压缩。

CONSISTENCY_UPGRADE
一致性、可靠性或合规要求提高。

ARCHITECTURE_EVOLUTION
单体、微服务、多租户或跨区域演进。

DESIGN_REVERSAL
要求删除或替换一个原有设计。
```

### 10.3.4 安全边界

- 不生成与用户 Claim 无关的随机高难题；
- 不因用户未答出反事实题，就否定其原始项目参与；
- 反事实主要影响迁移能力和架构权衡维度；
- 报告区分“原项目证据”和“新约束推理表现”。

### 10.3.5 验收标准

- 每道反事实题能指出来源事实和变化条件；
- 不修改原 Claim；
- 评分维度与普通项目事实题区分；
- 用户可以看到“原项目掌握”和“迁移能力”两个结果；
- 反事实问题不重复询问已确认事实。

---

## 10.4 Interview Setup

### 10.4.1 创建面试配置

```text
目标岗位
目标职级
面试轮次
重点能力
是否验证简历真实性
是否复验历史弱点
是否包含反事实题
预计轮数
强度：引导 / 标准 / 深挖
```

### 10.4.2 面试轮次策略

| 轮次     | 重点                     |
| -------- | ------------------------ |
| 简历面   | Claim、职责、结果数据    |
| 项目面   | 实现、接口、数据流、异常 |
| 技术面   | 原理、边界、故障、性能   |
| 系统设计 | 约束、权衡、演进、成本   |
| 综合复验 | 历史弱点、多形式和迁移   |

### 10.4.3 强度不是语气

- 引导：允许更多澄清和提示；
- 标准：正常追问；
- 深挖：减少提示，提高边界、故障和反事实比例。

不得只通过“更严厉的语言”模拟强度。

### 10.4.4 验收标准

- 配置真实影响 InterviewPlan；
- 同一配置可复现目标顺序；
- 面试轮次影响能力权重；
- 强度影响策略参数，而不仅改变 Prompt 语气；
- 配置保存到 Interview Snapshot。

---

## 10.5 同题重答与 Answer Diff

### 10.5.1 数据模型

```text
answer_versions
- id uuid pk
- question_id uuid
- parent_answer_id uuid nullable
- version_no int
- content text
- created_at timestamptz

answer_diffs
- id uuid pk
- previous_answer_id uuid
- current_answer_id uuid
- added_evidence jsonb
- removed_ambiguity jsonb
- new_contradictions jsonb
- score_changes jsonb
- prompt_version text
```

### 10.5.2 对比内容

- 新增了哪些可验证事实；
- 是否补充个人贡献；
- 是否说明指标来源；
- 是否解决原有矛盾；
- 是否只是复制 Coaching；
- 是否需要换题复验。

### 10.5.3 验收标准

- 原回答不可覆盖；
- Answer Diff 可追溯；
- 重答评分使用相同或明确标注的 Rubric；
- 仅复述参考答案不会直接提升 Ability Stability；
- 系统可建议换题验证。

---

## 10.6 Training Plan

### 10.6.1 目标

把报告中的问题转成可完成、可复验的训练任务。

### 10.6.2 任务类型

```text
EVIDENCE_COMPLETION
补充项目事实和数据来源。

CONCEPT_REVIEW
学习缺失的原理。

DESIGN_EXERCISE
完成一个架构或接口设计。

DEBUGGING_EXERCISE
完成故障排查题。

ANSWER_REWRITE
重写原回答。

TRANSFER_RETEST
在新场景中复验能力。
```

### 10.6.3 数据结构

```text
training_tasks
- id uuid pk
- user_id uuid
- source_interview_id uuid
- competency_code text nullable
- claim_id uuid nullable
- task_type text
- title text
- rationale text
- completion_criteria jsonb
- recommended_question_form text nullable
- status pending | completed | dismissed
- created_at timestamptz
- completed_at timestamptz nullable
```

### 10.6.4 示例

```text
任务：补充缓存性能数据证据
来源：Claim C2 / Verification Point VP5

需要完成：
1. 说明延迟指标是 P50、P95 还是平均值；
2. 说明测试环境和样本量；
3. 说明优化前后数据；
4. 说明由谁采集和验证。

完成标准：
下一次项目面试中能在不看提示的情况下说明以上四点。
```

### 10.6.5 验收标准

- 每个任务有明确来源；
- 每个任务有完成标准；
- 完成任务不等于能力自动通过；
- 下一场面试可选择优先复验已完成任务；
- 用户可关闭不适用任务。

---

# 11. Agent Loop 修改方案

## 11.1 新增状态字段

```python
class InterviewState(TypedDict):
    job_target_id: str | None
    competency_targets: list[str]
    claim_gap_targets: list[str]
    active_verification_point_id: str | None
    active_question_form: str | None
    target_reason_codes: list[str]
    historical_weaknesses: list[str]
    evidence_state_snapshot: dict
    question_form_history: list[dict]
    counterfactual_context: dict | None
    route_policy_version: str
    evidence_policy_version: str
    rubric_version: str
```

字段名称可根据现有代码调整，但语义必须保留。

## 11.2 推荐节点变化

```text
load_context
  → build_target_context          新增：加载岗位、历史弱点和 Claim Gap
  → select_verification_target    新增：规则排序
  → select_question_form          新增：避免重复形式
  → generate_question
  → receive_answer
  → analyze_answer
  → score_answer
  → update_evidence               修改：使用状态机
  → update_ability_observation    新增：记录能力观察
  → generate_coaching
  → decide_next                   修改：增加复验和反事实路由
  → generate_report
  → generate_training_plan        新增
```

## 11.3 路由枚举

```text
CLARIFY
DEEPEN
CHANGE_FORM
COUNTERFACTUAL
SWITCH_CLAIM
SWITCH_COMPETENCY
END
```

## 11.4 路由输入

路由策略只读取结构化字段：

- 当前 Evidence State；
- Relevance；
- Implementation Depth；
- Confidence；
- Clarification Count；
- Question Form History；
- Claim Priority；
- Competency Coverage；
- Remaining Turns；
- Historical Stability；
- Unresolved Contradiction。

不得直接让 LLM 输出“下一步做什么”后无校验执行。

## 11.5 路由示例

```python
def decide_next_route(ctx: RouteContext) -> RouteDecision:
    if ctx.has_unresolved_contradiction and ctx.clarification_count < 2:
        return RouteDecision.CLARIFY

    if ctx.evidence_state in {"ADDRESSED", "PARTIALLY_SUPPORTED"}:
        if ctx.current_form_count < 2 and ctx.remaining_turns >= 2:
            return RouteDecision.CHANGE_FORM

    if (
        ctx.evidence_state == "VERIFIED"
        and ctx.job_importance >= 0.8
        and ctx.transfer_status == "untested"
        and ctx.remaining_turns >= 2
    ):
        return RouteDecision.COUNTERFACTUAL

    if ctx.claim_turn_count >= ctx.max_claim_turns:
        return RouteDecision.SWITCH_CLAIM

    return RouteDecision.DEEPEN
```

### 11.6 验收标准

- 每个路由有 `reason_code`；
- 最大澄清次数严格生效；
- 反事实路由只针对高价值且已有基础证据的能力；
- 不同问题形式有历史记录；
- 路由单元测试覆盖所有分支；
- 面试不会因单个 Claim 无限循环。

---

# 12. 评分与置信度修改

## 12.1 保留六维评分

建议继续保留：

- Technical Correctness；
- Relevance；
- Implementation Depth；
- Personal Contribution；
- Production Awareness；
- Communication。

但第二阶段需增加三个独立概念：

```text
Score
回答质量。

Evidence State
该回答对 Verification Point 的支持程度。

Confidence
当前判断的可靠程度。
```

三者不得混为一个总分。

## 12.2 Question Form 权重

不同问题形式使用不同维度权重：

| Question Form  | 重点维度                                                     |
| -------------- | ------------------------------------------------------------ |
| CONCEPT        | Technical Correctness、Communication                         |
| PROJECT_DETAIL | Implementation Depth、Personal Contribution                  |
| DEBUGGING      | Technical Correctness、Production Awareness                  |
| TRADEOFF       | Technical Correctness、Implementation Depth、Production Awareness |
| COUNTERFACTUAL | Tradeoff Reasoning、Adaptability、Production Awareness       |
| TRANSFER       | Technical Correctness、Adaptability                          |

可以继续把最终加权分由代码计算，但建议为 Counterfactual 和 Transfer 新增独立指标，或只用于 Ability Profile，不强行塞入原六维总分。

## 12.3 评分版本

```text
rubrics
- key text
- version text
- question_form text
- role_family text
- level text
- dimension_weights jsonb
- descriptors jsonb
- status text
```

## 12.4 验收标准

- Total Score 由代码计算；
- 模型输出维度分必须通过范围校验；
- Score、Evidence State、Confidence 分别保存；
- 不同 Question Form 使用对应 Rubric；
- Report 不重新计算历史分数；
- 跨场次比较显示 Rubric 版本。

---

# 13. API 设计

## 13.1 Job Target

```http
POST   /api/v1/job-targets
GET    /api/v1/job-targets
GET    /api/v1/job-targets/{id}
PATCH  /api/v1/job-targets/{id}
DELETE /api/v1/job-targets/{id}
POST   /api/v1/job-targets/{id}/parse-jd
PATCH  /api/v1/job-targets/{id}/requirements/{requirement_id}
```

## 13.2 Claim Gap

```http
POST /api/v1/resumes/{resume_id}/claim-gap
GET  /api/v1/claim-gaps/{id}
POST /api/v1/claim-gaps/{id}/rebuild
```

返回示例：

```json
{
  "job_target_id": "uuid",
  "items": [
    {
      "claim_id": "uuid",
      "requirement_id": "uuid",
      "classification": "HIGH_PRIORITY_WEAK_EVIDENCE",
      "priority": 0.87,
      "reason_codes": [
        "HIGH_JOB_IMPORTANCE",
        "WEAK_EXISTING_EVIDENCE"
      ]
    }
  ]
}
```

## 13.3 Interview Setup

```http
POST /api/v1/interviews
GET  /api/v1/interviews/{id}/plan
POST /api/v1/interviews/{id}/answers
GET  /api/v1/interviews/{id}/events
POST /api/v1/answers/{answer_id}/retry
```

创建参数：

```json
{
  "resume_id": "uuid",
  "job_target_id": "uuid",
  "level": "mid",
  "round": "project",
  "focus_competencies": ["backend.cache", "backend.failure_recovery"],
  "retest_historical_weaknesses": true,
  "enable_counterfactual": true,
  "intensity": "standard",
  "max_turns": 12,
  "idempotency_key": "..."
}
```

## 13.4 Evidence

```http
GET /api/v1/interviews/{id}/claim-passports
GET /api/v1/claims/{claim_id}/evidence-timeline
GET /api/v1/interviews/{id}/coverage
```

## 13.5 Ability 与 Training Plan

```http
GET   /api/v1/abilities
GET   /api/v1/abilities/{competency_code}
GET   /api/v1/training-plans
PATCH /api/v1/training-tasks/{id}
POST  /api/v1/training-tasks/{id}/start-retest
```

## 13.6 通用要求

- 所有对象校验用户归属；
- 重要写接口支持 Idempotency Key；
- 错误返回稳定 Error Code；
- Prompt 和 Policy 版本不由前端任意指定；
- Evidence Span 的完整文本通过授权接口获取；
- 对不存在和无权限对象统一使用安全响应。

---

# 14. 数据库迁移顺序

建议按以下顺序增量迁移：

1. 新建 Competency Catalog；
2. 新建 Job Target 和 Job Requirement；
3. 新建 Claim—Competency、Claim—Requirement Mapping；
4. 为 Interview 增加岗位、职级、轮次和配置快照；
5. 新建 Verification Point；
6. 新建 Evidence State 和 Transition；
7. 为 Question 增加 Question Form 和 Target Reason；
8. 为 Evaluation 增加 Prompt、Rubric、Policy 版本；
9. 新建 Ability Observation 和 Ability Profile；
10. 新建 Answer Version、Answer Diff；
11. 新建 Training Task；
12. 新建 Prompt Version、Eval Case 和 Eval Run。

### 14.1 数据兼容原则

- 第一阶段历史 Interview 保持可查看；
- 旧 Claim 可在首次访问时按需创建 Verification Point；
- 旧 Evaluation 标记为 `rubric_version=phase1_legacy`；
- 旧报告不强制补算 Claim Gap；
- 新字段先 nullable，回填后再增加约束；
- 不通过迁移重新调用 LLM 改写旧数据。

---

# 15. 前端页面修改

## 15.1 新建面试页

新增：

- 目标岗位选择；
- JD 粘贴与解析；
- Requirement 编辑；
- 职级与轮次；
- 面试重点；
- 历史弱点复验；
- 反事实题开关；
- 面试强度与轮数。

## 15.2 InterviewPlan 预览

开始前展示：

```text
本次优先验证
1. Redis 一致性：岗位重要度高，现有证据弱
2. 消息幂等：简历存在 Claim，但责任边界不清
3. 故障恢复：目标岗位要求，本次尚未覆盖
```

不要展示完整题目，以免用户提前背答案。

## 15.3 面试房间

新增轻量信息：

- 当前验证目标；
- 当前问题形式；
- 当前面试进度；
- 是否正在澄清或反事实复验。

不建议实时展示分数和 Evidence State，以免用户迎合评分器。

## 15.4 报告页

优先级从高到低：

1. Claim Passport；
2. 岗位能力覆盖；
3. Evidence Timeline；
4. 待澄清和矛盾项；
5. 多形式复验结果；
6. 下一轮训练计划；
7. 六维评分；
8. 面试过程明细。

## 15.5 Ability 页面

每项能力展示：

- 当前等级；
- 稳定性；
- 迁移状态；
- 被验证的形式；
- 支持它的面试；
- 未解决缺口；
- 下一次建议题型。

## 15.6 前端验收标准

- 用户能理解“未覆盖”和“能力不足”的区别；
- Claim 状态可以定位到回答；
- 不同版本的回答可比较；
- 历史能力不只展示折线图；
- 面试配置确实影响计划；
- 核心页面具备组件测试和 E2E。

---

# 16. 测试方案

## 16.1 单元测试

重点覆盖：

- Claim Gap 分类；
- Target Priority；
- Evidence 状态机；
- VERIFIED 条件；
- Contradiction 澄清；
- Question Form 选择；
- 路由策略；
- Ability Stability；
- Training Task 生成规则；
- 加权评分。

### 示例：Evidence 状态机

```python
def test_verified_requires_traceable_span():
    ctx = EvidenceContext(
        current_state="PARTIALLY_SUPPORTED",
        relevance=92,
        technical_correctness=88,
        implementation_depth=84,
        confidence=0.94,
        evidence_spans=[],
        unresolved_contradiction=False,
    )

    decision = decide_transition(ctx)

    assert decision.to_state != "VERIFIED"
    assert decision.reason_code == "MISSING_TRACEABLE_EVIDENCE"
```

### 示例：未覆盖不等于能力不足

```python
def test_uncovered_requirement_is_not_scored_as_weakness():
    result = classify_requirement(
        requirement_importance=0.9,
        related_claims=[],
        observations=[],
    )

    assert result.classification == "UNCOVERED_REQUIREMENT"
    assert result.ability_score is None
```

### 示例：反事实路由条件

```python
def test_counterfactual_requires_existing_base_evidence():
    decision = decide_next_route(
        evidence_state="ADDRESSED",
        job_importance=0.9,
        transfer_status="untested",
        remaining_turns=4,
    )

    assert decision != "COUNTERFACTUAL"
```

## 16.2 集成测试

- JD 解析、编辑和保存；
- Resume + JobTarget 生成 Claim Gap；
- 创建 InterviewPlan；
- Answer → Evaluation → Evidence Transition；
- Evidence Timeline；
- Report 数据一致性；
- Answer Retry；
- Ability Observation 聚合；
- Training Plan 生成；
- 跨用户对象权限。

## 16.3 AI Eval

每次核心 Prompt 修改运行：

- Scoring Golden；
- Routing Golden；
- Evidence Golden；
- Contradiction Golden；
- Question Contract；
- Prompt Injection Smoke Cases。

## 16.4 E2E 主流程

```text
登录
→ 上传并确认简历
→ 选择岗位模板或粘贴 JD
→ 修改岗位要求
→ 查看 Claim Gap
→ 创建项目面试
→ 回答多个问题
→ 完成一次反事实复验
→ 查看 Claim Passport
→ 查看岗位覆盖
→ 查看 Training Plan
→ 重答一道题
→ 创建第二场复验面试
→ 查看 Ability Profile 变化
```

## 16.5 覆盖要求

| 范围                       | 建议最低要求 |
| -------------------------- | -----------: |
| Evidence 状态机            | 95% 分支覆盖 |
| Agent 路由                 | 90% 分支覆盖 |
| Claim Gap 与 Target Ranker |          90% |
| Ability Stability          |          90% |
| 其他核心后端模块           |          80% |
| 前端核心状态与表单         |          75% |
| E2E 关键路径               |     全部通过 |

---

# 17. 最低生产基础

第二阶段不是放弃生产质量，而是只做直接支撑核心功能的部分。

## 17.1 必须完成

- 用户数据归属；
- 对象级权限；
- 密码或现有身份凭据安全存储；
- 回答提交幂等；
- Checkpoint 恢复；
- LLM 超时和结构化输出失败处理；
- 日志脱敏；
- 简历大小和类型限制；
- 数据删除；
- 数据库迁移测试；
- 核心 CI；
- 基础 Token、延迟和失败率统计。

## 17.2 可以延后

- 邮箱验证完整链路；
- 多设备 Session 管理；
- 用户数据导出中心；
- 独立 Worker 集群；
- Dead Letter 管理后台；
- Redis Durable Event Store；
- 多实例 SSE Replay；
- 蓝绿发布；
- 完整 OpenTelemetry；
- 管理员查看用户数据；
- 复杂成本仪表盘。

若当前项目已经实现其中部分能力，应保留，不需要主动删除；但不再把它们作为第二阶段核心交付的阻塞项。

---

# 18. 里程碑与依赖顺序

## M2.0：范围收敛与基线冻结

### 工作

- 冻结第一阶段主流程；
- 记录现有 Prompt、Rubric 和路由版本；
- 建立首批 Eval Case；
- 确认 Competency Catalog；
- 清理第二阶段不做的需求。

### 完成定义

- 第一阶段 E2E 可重复运行；
- 所有现有 Prompt 有标识；
- 有可用于后续比较的基线结果；
- 团队不再并行开发语音、RAG、IDE 等功能。

## M2.1：岗位目标与 Claim Gap

### 工作

- Role Template；
- JD 结构化解析与编辑；
- Competency Catalog；
- Claim Mapping；
- Claim Gap；
- InterviewPlan Target Ranker；
- 新建面试配置页。

### 完成定义

- 用户可基于目标岗位创建面试；
- 计划可解释每个 Target；
- 报告能区分未覆盖与证据不足。

## M2.2：Evidence Engine 与可信报告

### 工作

- Verification Point；
- Evidence State Machine；
- Evidence Span；
- Transition Audit；
- Contradiction Clarification；
- Claim Passport；
- Evidence Timeline。

### 完成定义

- 所有 Claim 状态可追溯；
- VERIFIED 不再由单个模型布尔值决定；
- 报告能定位具体证据。

## M2.3：Evals 与评分校准

### 工作

- Prompt Registry；
- Rubric、Policy 版本；
- Scoring、Routing、Evidence Golden Dataset；
- Eval Runner；
- Regression Report；
- CI Eval Gate。

### 完成定义

- 修改 Prompt 前后可以量化比较；
- 关键退化能阻止发布；
- 历史面试保留实际版本。

## M2.4：多形式复验与反事实面试

### 工作

- Question Form；
- Form Selector；
- 重复问题检测；
- Counterfactual Templates；
- Route 扩展；
- 迁移能力观察。

### 完成定义

- 高价值能力可以被不同形式验证；
- 报告区分原项目证据与迁移表现；
- 不出现无依据的随机反事实题。

## M2.5：跨场次成长闭环

### 工作

- Ability Observation；
- Ability Profile；
- Stability；
- Answer Retry 与 Diff；
- Training Plan；
- 下一场面试复验入口。

### 完成定义

- 第二场面试可读取第一场未解决问题；
- 能判断单次表现与稳定表现；
- 训练任务有来源和完成标准。

## M2.6：小范围公测加固

### 工作

- 权限与删除；
- 核心 E2E；
- 错误处理；
- 日志脱敏；
- Token、延迟、失败率；
- 真实用户反馈入口；
- 修复阻塞问题。

### 完成定义

- 可邀请小范围用户完整使用；
- 核心数据无横向越权；
- 任务失败可恢复或安全重试；
- 用户能够理解报告结论。

---

# 19. 任务拆解建议

## 19.1 后端

- Competency Catalog 与版本；
- JD Parser Schema；
- Claim Mapper；
- Claim Gap Classifier；
- Target Ranker；
- Verification Point Generator；
- Evidence State Machine；
- Evidence Transition Repository；
- Question Form Selector；
- Counterfactual Generator；
- Ability Profile Aggregator；
- Training Plan Generator；
- Prompt Registry；
- Eval Runner；
- 数据权限和幂等。

## 19.2 前端

- Job Target 编辑器；
- Requirement 编辑器；
- Interview Setup；
- Plan Preview；
- Claim Gap；
- Claim Passport；
- Evidence Timeline；
- JD Coverage；
- Answer Diff；
- Ability Profile；
- Training Plan。

## 19.3 数据与评测

- Competency 等级描述；
- Scoring 标注；
- Routing 标注；
- Evidence 状态标注；
- Contradiction 样本；
- Question Contract；
- 反事实问题质量样本；
- 版本基线报告。

---

# 20. 第二阶段验收指标

## 20.1 产品验收

- [ ] 用户可选择目标岗位、职级和面试轮次；
- [ ] 用户可粘贴并编辑 JD；
- [ ] 系统能生成 Claim Gap；
- [ ] InterviewPlan 可解释 Target 来源；
- [ ] 每个 Claim 具有 Verification Point；
- [ ] Evidence 状态变化可追溯；
- [ ] 报告展示 Claim Passport；
- [ ] 报告区分未覆盖、未支持和矛盾；
- [ ] 支持多形式复验；
- [ ] 支持反事实面试；
- [ ] 支持同题重答和版本对比；
- [ ] 支持跨场次 Ability Profile；
- [ ] 支持下一轮 Training Plan。

## 20.2 可信性验收

- [ ] VERIFIED 必须有 Evidence Span；
- [ ] 所有状态变化有 Policy Version；
- [ ] 所有分数有 Rubric 和 Prompt Version；
- [ ] 未覆盖能力不计为零分；
- [ ] 矛盾判断有澄清路径；
- [ ] Report 不重新计算评分；
- [ ] Prompt 修改可运行回归 Eval；
- [ ] 关键退化可以阻止发布。

## 20.3 工程验收

- [ ] 核心对象具有用户归属；
- [ ] 回答提交幂等；
- [ ] Checkpoint 恢复可用；
- [ ] LLM 非法输出安全失败或重试；
- [ ] 数据库可从第一阶段迁移；
- [ ] 日志不记录密码、Token、完整简历和完整回答；
- [ ] 主流程 E2E 全部通过；
- [ ] Evidence、Routing 和 Claim Gap 达到规定测试覆盖率。

## 20.4 用户价值验收

小范围公测用户应能够回答：

- 系统为什么问我这道题；
- 哪些简历 Claim 已被支持；
- 哪些地方仍然缺证据；
- 哪些目标岗位能力尚未覆盖；
- 为什么某项能力被判定为不稳定；
- 下一次应该练什么；
- 第二次面试相比第一次真正改善了什么。

如果用户只能看到总分和通用建议，即使系统更稳定，也不能视为第二阶段完成。

---

# 21. Definition of Done

任一核心功能只有同时满足以下条件才视为完成：

1. 业务对象和状态定义清晰；
2. 规则层与 LLM 职责分离；
3. Prompt、Rubric 或 Policy 已版本化；
4. 数据库迁移已提供；
5. API Schema 已更新；
6. 用户归属和权限已校验；
7. 单元测试覆盖关键分支；
8. 至少有一个集成测试；
9. 前端能够展示核心结果；
10. 错误信息不泄露内部实现；
11. 文档已更新；
12. 不造成 Golden Eval 的阻塞性退化。

---

# 22. 主要风险与应对

| 风险                    | 影响         | 应对                                    |
| ----------------------- | ------------ | --------------------------------------- |
| Competency Catalog 过大 | 开发失控     | 第二阶段只覆盖后端与 Agent 工程         |
| JD 解析误差             | 面试目标错误 | 用户确认与编辑，不直接采用模型结果      |
| Claim Mapping 不稳定    | 问题偏离简历 | 保存 Mapping Reason，并允许用户修正     |
| Evidence 状态过于复杂   | 用户难以理解 | 状态数量固定，报告使用自然语言解释      |
| VERIFIED 误判           | 结论不可信   | Evidence Span、Policy、Golden Eval      |
| 矛盾误报                | 伤害用户信任 | 先澄清，再确认，避免诚信标签            |
| 第二次回答背诵 Coaching | 虚假进步     | 换题、多形式和迁移复验                  |
| 跨版本分数不可比        | 趋势误导     | 标注 Rubric 版本，必要时分开展示        |
| 反事实题脱离项目        | 变成随机难题 | 必须绑定已确认事实与 Verification Point |
| 基础设施继续膨胀        | 核心能力延期 | 按“是否直接支撑 P0/P1”决定是否开发      |

---

# 23. 最终交付物

第二阶段结束时，应交付：

```text
1. 目标岗位与 JD 结构化模块
2. 后端与 Agent Competency Catalog
3. Claim—Requirement Mapping
4. Claim Gap 与可解释 InterviewPlan
5. Evidence Engine 2.0
6. Verification Point 与 Evidence Transition
7. Claim Passport 与 Evidence Timeline
8. Prompt、Rubric、Policy 版本体系
9. Scoring、Routing、Evidence Golden Dataset
10. Eval Runner 与回归报告
11. Question Form 与多形式复验
12. Counterfactual Interview
13. Ability Observation 与 Ability Profile
14. 同题重答与 Answer Diff
15. Training Plan
16. 新建面试配置页
17. 报告和 Analytics 改版
18. 核心 E2E 与权限测试
19. 数据库迁移说明
20. 小范围公测验收报告
```

明确不要求交付：

```text
复杂 RAG
向量数据库
实时语音
摄像头分析
在线 IDE
求职岗位爬虫
企业招聘排名
大型管理后台
多 Agent 协商系统
```

---

# 24. 结论

Wenjian 第二阶段不应继续横向增加“更多题型、更多模型、更多交互形式”，而应围绕以下核心闭环开发：

```text
目标岗位
  → Claim Gap
  → 可解释 InterviewPlan
  → 多形式动态追问
  → Evidence 状态机
  → Claim Passport
  → 跨场次能力复验
  → 下一轮训练计划
```

第二阶段真正需要建立的壁垒不是 RAG、语音或页面数量，而是：

> **每道问题有明确验证目标，每个判断有可追溯证据，每次训练能在下一场面试中被重新验证。**

当用户能够清楚看到“我写在简历上的哪些内容已经讲清楚、哪些仍缺证据、目标岗位还缺什么、下一场应该如何复验”时，Wenjian 才真正从普通 AI 模拟面试项目升级为证据驱动的面试训练系统。