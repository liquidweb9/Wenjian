# 问鉴（Wenjian）项目文档

本目录描述当前仓库中已经实现的功能、接口、Agent 工作循环和 React 前端效果。文档以当前代码为准；规划中的能力会明确标记为“未实现”或“有限支持”。

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [当前实现与产品效果](./current-implementation.md) | 系统目标、已完成工作、端到端流程、鉴权、岗位目标、证据、能力档案、训练计划、数据持久化、恢复能力、当前限制 |
| [API 接口文档](./api-reference.md) | 所有 `/api/v1` 接口、请求参数、预期返回、错误格式和 SSE 事件 |
| [Agent Loop 与决策机制](./agent-loop.md) | LangGraph 节点、状态、暂停/恢复、深挖与切换项目规则、评分和报告生成 |
| [React 前端页面与交互](./frontend-pages.md) | 页面路由、页面效果、页头与返回导航规范、加载体验、实时状态、刷新恢复、品牌和布局 |

## 一句话概览

问鉴是一套“简历证据驱动”的 AI 模拟面试系统：用户上传并确认真实简历后，系统提取项目经历和可验证主张，定义目标岗位与能力需求，通过 LangGraph 连续提问、分析、评分、维护证据状态，并生成逐题教练反馈、最终报告、跨场次能力档案和可执行的训练计划。

## 已实现能力

- **真实账号体系**：注册 / 登录 / 当前用户，JWT Bearer Token，全部数据按用户隔离。
- **简历处理**：PDF / TXT / TEX 解析与标准化，人工检查修订，Profile 与可验证主张提取。
- **岗位目标目录**：模板、JD 解析（AI 提取需求）、手动三种创建方式，25 项后端/Agent 能力目录。
- **能力缺口分析**：对比简历声明与岗位需求，识别未覆盖、弱证据、矛盾三类缺口并排序。
- **动态模拟面试**：LangGraph 连续追问（深挖 / 澄清 / 切换项目），六维评分与逐题教练反馈。
- **证据状态机**：验证点 `UNSEEN → ADDRESSED → PARTIALLY_SUPPORTED → VERIFIED`，矛盾检测与澄清。
- **能力档案与训练计划**：跨场次能力聚合、稳定性与迁移验证，按证据缺口生成训练任务。
- **报告与统计**：逐题报告、主张护照、覆盖视图、Dashboard 与能力分析趋势。

## 当前技术栈

- 后端：FastAPI、SQLAlchemy 2.0 Async、PostgreSQL、LangGraph、Pydantic。
- 鉴权：JWT Bearer Token，用户作用域数据隔离。
- LLM：Agnes OpenAI-compatible API，平台统一配置，任务级档位路由（auto / fast / balanced / judge）。
- 前端：React 19、TypeScript、Vite、TanStack Query、Zustand、Lucide Icons。
- 实时通信：基于 `fetch + ReadableStream` 的 SSE，指数退避重连与详情轮询兜底。
- 文件解析：PDF、TXT、TEX，输出标准化文本、结构块和抽取质量。

## 入口

- FastAPI OpenAPI：启动后访问 `http://localhost:8000/docs`。
- React 开发服务器：默认 `http://localhost:5174`。
- API 基础路径：`/api/v1`。

