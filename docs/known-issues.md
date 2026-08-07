# 现存问题清单

本文档记录已知问题与待办事项，供后续修复时参考。每条包含问题描述、影响范围、证据与建议修复方向。

## 1. 模拟面试与练习模式完全无差别

**状态**：待修复（2026-08-07 记录）

**问题描述**：前端创建面试页的「模拟面试 / 练习模式」二选一与设置页的默认模式下拉、面试列表页的模式过滤，均只把 `mode` 字符串传给后端，但后端 LangGraph 图逻辑对两种模式执行完全相同的代码路径，行为无任何差异。

**影响范围**：

- 用户无法通过选择「练习模式」获得更轻量的体验（UI 文案宣称「练习模式更轻量，模拟面试更接近真实流程」，但无对应实现）。
- 面试列表页的「全部模式」下拉过滤无效：前端 `interview-list-page.tsx` 发送 `mode` 参数，但后端 `list_interviews` 接口只接收 `status` 和 `resume_id`，`mode` 被 FastAPI 静默忽略。

**证据**：

- `app/persistence/models.py:136` — `mode` 仅为字符串列，默认 `"simulation"`。
- `app/interview/state.py:16` — `interview_mode` 声明后无任何图节点读取。
- `app/core/enums.py:64` — `InterviewMode` 定义了 `simulation / practice / assessment`，其中 `assessment` 为死代码，从未使用。
- `app/api/v1/interviews.py:56-63` — `CreateInterviewRequest.mode` 为自由字符串，未按 `InterviewMode` 校验。
- `app/interview/nodes/*.py` 中的 `mode` 匹配全部是 `model_dump(mode="json")`，与面试模式无关。
- 前端 `interview-create-page.tsx:233-248`、`settings-page.tsx:18-25`、`interview-list-page.tsx:20-23,70-79`。

**建议修复方向**：

1. 在图中读取 `state["interview_mode"]` 分支，例如在 `build_plan`、`rules.py` / `decide_next`、`generate_question` 中区分行为（如练习模式减少追问深度、更短问题等）。
2. 收紧 `CreateInterviewRequest.mode`，用 `InterviewMode` 枚举校验非法值。
3. 让 `list_interviews` 支持 `mode` 查询参数，修复前端过滤下拉的假过滤问题。

## 生产化后续（路线 1 平台统一 Key）

**背景**：已按路线 1 完善——平台统一 Key，用户只选档位（auto/fast/balanced/judge），Token/温度归平台环境配置。以下为真实生产落地仍需补的项。

- **用量计费**：记录每次 LLM 调用的 input/output tokens（`agnes_api.py` 已在日志输出），需要聚合到 Interview / User 维度，支持对账与配额。
- **限流（Rate Limiting）**：按用户/接口做令牌桶或滑动窗口限流，防止单用户打爆平台 Key 预算。
- **Key 轮换与密钥管理**：`LLM_API_KEY` 从明文 `config.env` 迁移到 Secret Manager / Vault，支持密钥轮换不中断服务。
- **档位上限（可选）**：按用户套餐限制可选档位（如免费用户最高 balanced），避免用户都选 judge 拉高成本。
- **model_tier 落库**：当前 `model_tier` 仅存在 LangGraph state（`InterviewState.model_tier`），进程重启丢失 checkpointer 后回落 `auto`。需加 `Interview.model_tier` 列 + 迁移，并在恢复路径（`_ensure_graph_checkpoint`）读回。
- **模型档位配置页**：后端提供只读的模型档位 → 实际模型名映射（`MODEL_TIER_MAP`），前端设置页展示当前生效的模型名。

