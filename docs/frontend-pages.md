# React 前端页面与交互

## 1. 前端架构

- React 19 + TypeScript Strict。
- Vite 按页面 Lazy Load。
- TanStack Query 管理服务端状态和缓存失效。
- Zustand Persist 管理侧边栏、用户偏好、回答草稿和待处理提交。
- Axios 统一错误模型并注入 `X-Request-ID`。
- SSE 使用 `fetch + ReadableStream`，便于自行控制重连和消息解析。
- CSS 以全局 Design Tokens 和页面内 `React.CSSProperties` 为主。

## 2. 页面路由

| 路由 | 页面 | 当前效果 |
| --- | --- | --- |
| `/login` | 登录 | 真实鉴权（JWT），已登录自动跳转工作台 |
| `/register` | 注册 | 创建账号后自动登录进入工作台 |
| `/app/dashboard` | 工作台 | 汇总简历、待确认、面试、进行中记录和平均分 |
| `/app/resumes` | 简历列表 | 分页、搜索、状态筛选、进入详情/上传 |
| `/app/resumes/new` | 简历上传 | PDF/TXT/TEX 上传，展示解析进度和错误 |
| `/app/resumes/:resumeId/review` | 解析检查 | 查看并修改标准化文本，确认 Revision |
| `/app/resumes/:resumeId/profile` | Profile | 展示结构化教育、工作、项目、研究和技能 |
| `/app/resumes/:resumeId/claims` | Claims | 查看面试主张、优先级、风险和验证点 |
| `/app/resumes/:resumeId/ability-profile` | 能力档案 | 跨场次能力聚合、稳定性与迁移验证 |
| `/app/resumes/:resumeId/training-plan` | 训练计划 | 生成/查看证据补强任务，支持复验 |
| `/app/interviews` | 面试记录 | 列出进行中/已完成面试并继续或查看报告 |
| `/app/interviews/new` | 创建面试 | 选择简历、岗位、模式、轮次、JD、模型档位 |
| `/app/interviews/:id/live` | 面试房间 | 实时问题、回答、历史、评分、Coaching、恢复 |
| `/app/interviews/:id/report` | 面试报告 | 总结、能力、逐题、Claim、正文和导出 |
| `/app/job-targets` | 目标岗位管理 | 岗位卡片列表、创建入口 |
| `/app/job-targets/create` | 创建目标岗位 | 模板 / JD 解析 / 空白三种方式 |
| `/app/job-targets/:jobTargetId` | 目标岗位详情 | 查看/编辑岗位与能力需求 |
| `/app/claim-gap/:resumeId/:jobTargetId` | 能力缺口分析 | 简历声明与岗位需求覆盖对比 |
| `/app/analytics` | 能力分析 | 分数分布、强弱项、Claim 验证率和趋势 |
| `/app/settings` | 设置 | 默认模式、默认最大轮次、模型档位、教练开关 |
| `*` | 404 | 未找到页面 |

## 3. 页面页头与返回导航规范（统一模式）

所有 `AppLayout` 下的页面统一使用共享 `PageHeader` 组件，规则如下：

| 页面类型 | 页头形态 | 返回按钮 | Logo |
| --- | --- | --- | --- |
| 管理/列表页（工作台、简历管理、模拟面试、目标岗位、能力分析、设置） | `PageHeader`（标题 + 描述）+ 右上 `btn-primary` 创建按钮 | 无 | 无 |
| 创建页（上传简历、创建面试、创建目标岗位） | `PageHeader`（brand + 标题 + 描述） | 左上角「返回列表」 | 有 |
| 详情/分析页（解析确认、画像、主张、能力档案、训练计划、岗位详情、能力缺口） | `PageHeader`（brand + 标题 + 描述）+ `action` 槽 | 左上角「返回上一步」 | 有 |

- 返回导航统一为 `BackButton` 组件（`components/common/back-button.tsx`）：箭头图标 + 文字，`alignSelf: "flex-start"` 防止在页头中拉伸。
- 页面已移除自定义面包屑；顶部「Wenjian Workspace」+ 当前页标题由 `Topbar` 统一渲染，`PAGE_TITLES`（`lib/brand.ts`）维护标题映射。
- 加载/错误/空态统一使用 `LoadingState` / `ErrorState` / `EmptyState` 共享组件。
- 例外：面试房间（全屏三栏）与面试报告页保留自有头部布局。

## 4. 全局布局和品牌

### 主应用

- 左侧为深色品牌 Sidebar。
- Sidebar 高度固定为 `100dvh`，页面上下滚动时不跟随内容滚动。
- 主内容区使用独立 `overflow: auto`。
- Sidebar 支持折叠，折叠时显示 Mark 和图标。
- Topbar 提供当前页面、导航和折叠控制。

### 品牌规范

| Token | 值 | 用途 |
| --- | --- | --- |
| Primary Navy | `#0D1B2A` | 主按钮、侧边栏、主品牌 |
| Secondary Teal | `#0EA5A0` | 链接、状态、强调 |
| Accent Cyan | `#22C1C3` | 渐变、动态图形 |
| Page Background | `#F7F8FA` | 页面底色 |
| Surface | `#FFFFFF` | 卡片 |
| Text Primary | `#0F172A` | 正文标题 |
| Text Secondary | `#475569` | 辅助文案 |
| Border | `#E2E8F0` | 描边与分割 |

Logo 使用品牌 SVG 中的 W + 对话/问题图形，提供浅色和深色背景版本。

## 5. 创建面试页

用户配置：

- 已确认简历。
- 目标岗位。
- 模拟面试或练习模式。
- 最大轮次。
- 可选岗位 JD。

轮次输入支持 3–30，提供 10、15、20、25、30 快捷按钮。页面明确说明：

- 15 轮只是默认值。
- 系统可能提前结束。
- 深挖还是切换项目由证据、回答质量和项目覆盖决定。

提交成功后自动导航到 Live Room。

## 6. 面试房间

### 三栏结构

左栏：

- 当前进度、模式、连接状态、阶段和事件序号。
- 历史问答列表及每题总分。
- 点击历史题进入评分和教练建议回看。

中栏：

- 当前问题。
- 回答输入框和自动保存提示。
- 分阶段加载体验。
- 六维评分、优点、缺失项。
- 反馈与改进建议。
- “预期回答（强回答示例）”。
- 完成后进入报告页。

右栏：

- 目标岗位和运行状态。
- 当前问题来源与快照。
- 系统如何决定“继续深挖或切换项目”。
- 刷新和离开页面后的恢复说明。

### 运行阶段

```text
loading
  -> connecting
  -> waiting_for_question
  -> answering
  -> submitting / analyzing
  -> answering 或 finished
```

### 加载效果

- 恢复现场和生成下一题使用大型品牌化 Loading Card。
- 显示三阶段工作说明和等待秒数。
- 回答分析展示：
  1. 理解回答。
  2. 证据核验。
  3. 多维评分。
  4. 预期回答。
- 使用进度扫光、浮动图标和完成状态卡片。
- 文案说明用户可以暂时离开，返回后自动恢复。

### 预期回答

前端优先读取：

```text
coaching.expert_answer
coaching.complete_answer
```

并展示为“预期回答（强回答示例）”。页面同时提示：

- 示例是题目考察点和回答框架。
- 不是候选人已经陈述的项目事实。
- 用户应使用自己的真实经历补全。

## 7. SSE Runtime

### 连接状态

```text
idle -> connecting -> connected
                     -> disconnected -> reconnecting
                                      -> failed
```

- 首次连接显示 `connecting`。
- 断开后按 1s、2s、4s……最大 15s 退避。
- 最多重试 10 次。
- 前端 reducer 使用 Sequence 去重。
- `_connection_change` 是前端内部事件，不参与 Sequence 去重。

### 事件到 UI 的映射

| SSE Event | UI 变化 |
| --- | --- |
| `interview.initialized` | 等待问题 |
| `question.ready` | 显示新问题，清空上一轮实时评分/Coaching |
| `answer.accepted` | 进入分析状态 |
| `analysis.completed` | 保持分析状态 |
| `scoring.completed` | 展示评分 |
| `coaching.ready` | 展示反馈和预期回答 |
| `interview.finished` | 展示完成页 |
| `report.ready` | 刷新详情并可进入报告 |

## 8. 刷新、退出和重复提交保护

### 草稿

- 输入时实时写入 Zustand Persist。
- Key 为 `${interviewId}_${questionId}`。
- 回到同一道题时恢复草稿。
- 服务端成功处理回答后清除。

### Pending Submission

- 点击提交时生成稳定的 `crypto.randomUUID()` 幂等键。
- 幂等键和问题 ID 持久化到 LocalStorage。
- 刷新后如果该题仍标记为 Pending，页面显示恢复/分析状态，不再次显示可提交输入框。
- 轮询发现历史中已有该 Question 的 Answer 后清除 Pending 标记。
- 同一次待处理回答重试时复用原幂等键。

### 服务端状态补偿

- SSE 是低延迟路径。
- 未完成面试每 5 秒轮询详情。
- SSE 重连会收到当前 Question 或 Finished Snapshot。
- 因此刷新、浏览器 Tab 挂起或短时丢事件不会只依赖单一实时连接。

## 9. 报告与分析页

报告数据包括：

- Overall Score。
- Questions Asked / Answered。
- Ability Scores。
- Question Details。
- Evaluation 和 Analysis。
- Claim Statuses。
- Contradictions。
- Coverage。
- LLM 报告正文。

Analytics 页面聚合：

- 五档分数区间。
- Top 3 和 Weak 3 能力。
- Claim Verification Rate。
- 每周面试数量。
- 已完成面试分数趋势。

## 10. 当前前端限制

- SSE 不是 Token Streaming。
- 页面主要使用 Inline Style，页头/导航/状态组件已抽取为共享组件，其余页面样式后续可继续抽取和加入响应式断点。
- Live Room 三栏布局主要面向桌面端，移动端还需要专门的信息架构。
- 尚未加入完整的 E2E、视觉回归和 Screen Reader 自动测试。

