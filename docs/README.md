# 问鉴（Wenjian）项目文档

本目录描述当前仓库中已经实现的功能、接口、Agent 工作循环和 React 前端效果。文档以当前代码为准；规划中的能力会明确标记为“未实现”或“有限支持”。

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [当前实现与产品效果](./current-implementation.md) | 系统目标、已完成工作、端到端流程、数据持久化、恢复能力、当前限制 |
| [API 接口文档](./api-reference.md) | 所有 `/api/v1` 接口、请求参数、预期返回、错误格式和 SSE 事件 |
| [Agent Loop 与决策机制](./agent-loop.md) | LangGraph 节点、状态、暂停/恢复、深挖与切换项目规则、评分和报告生成 |
| [React 前端页面与交互](./frontend-pages.md) | 页面路由、页面效果、加载体验、实时状态、刷新恢复、品牌和布局 |

## 一句话概览

问鉴是一套“简历证据驱动”的 AI 模拟面试系统：上传并确认简历后，系统提取项目经历和可验证主张，构建项目级 InterviewPlan，通过 LangGraph 连续提问、分析、评分、维护证据状态，并生成逐题教练反馈与最终报告。

## 当前技术栈

- 后端：FastAPI、SQLAlchemy 2.0 Async、PostgreSQL、LangGraph、Pydantic。
- LLM：Agnes OpenAI-compatible API，通过任务路由选择 fast / balanced / judge 模型层级。
- 前端：React 19、TypeScript、Vite、TanStack Query、Zustand、Tailwind CSS 4、Lucide Icons。
- 实时通信：基于 `fetch + ReadableStream` 的 SSE。
- 文件解析：PDF、TXT、TEX，输出标准化文本、结构块和抽取质量。

## 入口

- FastAPI OpenAPI：启动后访问 `http://localhost:8000/docs`。
- React 开发服务器：默认 `http://localhost:5174`。
- API 基础路径：`/api/v1`。

