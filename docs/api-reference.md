# API 接口文档

## 1. 通用约定

- Base URL：`/api/v1`
- 默认请求与响应：`application/json`
- 文件上传：`multipart/form-data`
- 实时事件：`text/event-stream`
- 分页从 1 开始。
- 时间字段为 ISO 8601 字符串。
- ID 是不透明字符串，调用方不应解析其内部格式。
- 除 `/register`、`/login`、`/health` 外，其余接口均需 Bearer Token：`Authorization: Bearer <access_token>`。

启动后可访问 FastAPI 自动文档：

- Swagger UI：`http://localhost:8000/docs`
- OpenAPI JSON：`http://localhost:8000/openapi.json`

### 1.1 Request ID

前端会给每个 Axios 请求注入：

```http
X-Request-ID: 12-char-uuid
```

错误响应会回传对应的 `request_id`。

### 1.2 分页返回

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### 1.3 错误返回

普通 HTTP 错误：

```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Resume not found",
    "request_id": "a1b2c3d4e5f6"
  }
}
```

参数校验错误：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "field_errors": [
      {
        "field": "query.page_size",
        "code": "less_than_equal",
        "message": "Input should be less than or equal to 100"
      }
    ],
    "request_id": "a1b2c3d4e5f6"
  }
}
```

前端将错误统一转换为 `ApiError(status, code, message, requestId, fieldErrors)`。

## 2. 接口总表

| Method | Path | 作用 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| POST | `/register` | 注册账号 |
| POST | `/login` | 登录并获取 Token |
| GET | `/me` | 当前用户 |
| DELETE | `/me` | 注销账号并删除数据 |
| DELETE | `/resumes/{resume_id}` | 删除指定用户的简历 |
| DELETE | `/interviews/{interview_id}` | 删除指定用户的面试 |
| DELETE | `/job-targets/{job_target_id}` | 删除指定用户的岗位目标 |
| GET | `/resumes` | 简历列表 |
| POST | `/resumes` | 上传简历文件 |
| POST | `/resumes/text` | 上传纯文本简历 |
| GET | `/resumes/{resume_id}` | 简历详情 |
| PATCH | `/resumes/{resume_id}/revisions/{revision_id}` | 修改未确认 Revision |
| POST | `/resumes/{resume_id}/revisions/{revision_id}/confirm` | 确认并生成 Profile/Claims |
| GET | `/resumes/{resume_id}/revisions` | Revision 历史 |
| GET | `/resumes/{resume_id}/claims` | 获取 Claims |
| PATCH | `/resumes/{resume_id}/claims/{claim_id}` | 更新 Claim |
| PATCH | `/resumes/{resume_id}/target-role` | 保存/修改目标岗位（重新排序主张） |
| GET | `/interviews` | 面试列表 |
| POST | `/interviews` | 创建面试并生成第一题 |
| GET | `/interviews/{interview_id}` | 面试详情与历史 |
| GET | `/interviews/{interview_id}/events` | SSE 实时事件 |
| POST | `/interviews/{interview_id}/answers` | 提交回答并运行 Agent Loop |
| POST | `/interviews/{interview_id}/finish` | 主动结束并生成报告 |
| GET | `/interviews/{interview_id}/report` | 获取报告 |
| POST | `/interviews/{interview_id}/report/export` | 导出 JSON/Markdown |
| GET | `/interviews/{interview_id}/questions/{question_id}/versions` | 回答版本历史（答案对比） |
| GET | `/job-targets` | 岗位目标列表 |
| POST | `/job-targets` | 创建岗位目标 |
| POST | `/job-targets/parse-jd` | 解析 JD 生成能力需求 |
| GET | `/job-targets/{job_target_id}` | 岗位目标详情 |
| PATCH | `/job-targets/{job_target_id}` | 更新岗位目标 |
| POST | `/claim-gap` | 触发能力缺口分析 |
| GET | `/claim-gap/resume/{resume_id}/job-target/{job_target_id}` | 获取能力缺口分析结果 |
| GET | `/evidence/verification-points/{claim_id}` | 主张的验证点与证据状态 |
| GET | `/evidence/transitions/{verification_point_id}` | 验证点迁移历史 |
| GET | `/evidence/contradictions/{interview_id}` | 面试矛盾列表 |
| GET | `/evidence/evidence/{verification_point_id}` | 验证点证据片段 |
| GET | `/abilities/profile/{resume_id}` | 跨场次能力档案 |
| GET | `/training-plans` | 训练任务列表 |
| POST | `/training-plans/{resume_id}/generate` | 生成训练计划 |
| PATCH | `/training-plans/{task_id}` | 更新训练任务状态 |
| GET | `/dashboard/summary` | 工作台汇总 |
| GET | `/analytics/summary` | 能力与分数聚合 |
| GET | `/analytics/trends` | 面试与分数趋势 |

## 3. 系统接口

### GET `/health`

预期返回：

```json
{
  "status": "ok",
  "version": "0.1.0",
  "env": "development",
  "model": "agnes-2.5-flash"
}
```

## 4. 鉴权接口

### POST `/register`

请求：

```json
{
  "email": "candidate@example.com",
  "password": "secret123",
  "full_name": "张三"
}
```

预期返回：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

注册成功后即返回 Token，可直接用于后续请求。

### POST `/login`

请求：

```json
{
  "email": "candidate@example.com",
  "password": "secret123"
}
```

预期返回与注册相同。

### GET `/me`

预期返回：

```json
{
  "user_id": "usr_xxx",
  "email": "candidate@example.com",
  "full_name": "张三",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-08-01T10:00:00",
  "last_login_at": "2026-08-07T09:00:00"
}
```

### DELETE `/me`

注销账号并删除当前用户的全部数据。预期返回删除统计：

```json
{
  "training_tasks": 2,
  "ability_profiles": 1,
  "ability_observations": 6,
  "interviews": 4,
  "resumes": 2,
  "job_targets": 3,
  "llm_calls_anonymized": 120,
  "llm_calls_deleted": 5,
  "user_deleted": true,
  "message": "账号与关联数据已删除"
}
```

## 5. 简历接口

### GET `/resumes`

Query：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `page` | 1 | 页码，最小 1 |
| `page_size` | 20 | 每页 1–100 |
| `search` | null | 按文件名模糊搜索 |
| `status` | null | Revision 状态 |
| `sort_by` | `created_at` | `created_at` 或文件名 |
| `sort_order` | `desc` | `asc` / `desc` |

预期返回：

```json
{
  "items": [
    {
      "resume_id": "res_xxx",
      "file_name": "candidate.pdf",
      "source_type": "pdf",
      "created_at": "2026-07-27T10:00:00",
      "status": "CONFIRMED",
      "latest_revision_id": "rev_xxx"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### POST `/resumes`

Content-Type：`multipart/form-data`

字段：

```text
file=<PDF/TXT/TEX binary>
```

预期返回：

```json
{
  "resume_id": "res_xxx",
  "revision_id": "rev_xxx",
  "status": "PARSED_UNCONFIRMED",
  "source_type": "pdf",
  "extraction_quality": 0.91,
  "extraction_warnings": [],
  "normalized_text": "标准化后的简历文本",
  "blocks": [
    {
      "block_id": "blk_xxx",
      "text": "项目经历",
      "raw_text": "项目经历",
      "block_type": "heading",
      "source_location": {},
      "style_hints": {},
      "warnings": []
    }
  ]
}
```

### POST `/resumes/text`

请求：

```json
{
  "file_name": "resume.txt",
  "text": "姓名...\n项目经历..."
}
```

返回结构与文件上传相同。

### GET `/resumes/{resume_id}`

预期返回：

```json
{
  "resume_id": "res_xxx",
  "file_name": "candidate.pdf",
  "source_type": "pdf",
  "status": "CONFIRMED",
  "revision_id": "rev_xxx",
  "latest_revision_id": "rev_xxx",
  "normalized_text": "...",
  "raw_text": "...",
  "extraction_quality": 0.91,
  "extraction_warnings": [],
  "extraction_method": "pymupdf",
  "parser_name": "PdfParser",
  "parser_version": "1.0",
  "profile": {
    "candidate_name": "候选人",
    "experiences": [],
    "projects": [],
    "research": [],
    "skills": []
  },
  "created_at": "2026-07-27T10:00:00"
}
```

不存在时返回 404。

### PATCH `/resumes/{resume_id}/revisions/{revision_id}`

仅允许修改未确认 Revision。

请求：

```json
{
  "normalized_text": "用户检查并修改后的完整文本"
}
```

预期返回：

```json
{
  "resume_id": "res_xxx",
  "revision_id": "rev_xxx",
  "normalized_text": "...",
  "extraction_quality": 0.95,
  "extraction_warnings": []
}
```

已确认或已被替代的 Revision 返回 400。

### POST `/resumes/{resume_id}/revisions/{revision_id}/confirm`

可选 Query：

```text
target_role=高级后端工程师
```

操作效果：

1. 构建 Profile。
2. 提取 Claims。
3. 替换该简历旧 Claims。
4. 将 Revision 标记为 `CONFIRMED`。

预期返回：

```json
{
  "resume_id": "res_xxx",
  "revision_id": "rev_xxx",
  "status": "CONFIRMED",
  "profile": {
    "resume_id": "res_xxx",
    "revision_id": "rev_xxx",
    "candidate_name": "候选人",
    "headline": "Backend Engineer",
    "education": [],
    "experiences": [],
    "projects": [],
    "research": [],
    "competitions": [],
    "skills": ["Python", "PostgreSQL"],
    "extraction_confidence": 0.9,
    "warnings": []
  },
  "claims": [
    {
      "claim_id": "clm_xxx",
      "entry_id": "entry_xxx",
      "claim_text": "设计并实现异步任务系统",
      "claim_type": "implementation",
      "technologies": ["Python"],
      "expected_level": "use",
      "verification_points": [
        {
          "point_id": "vp_xxx",
          "description": "解释任务幂等与重试设计",
          "category": "implementation",
          "target_depth": 4,
          "importance": 8
        }
      ],
      "risk_flags": [],
      "priority": 82,
      "confidence": 0.88
    }
  ]
}
```

LLM 临时不可用且无法产生有效 Profile 时返回 503，并尽量保留旧 Profile。

### GET `/resumes/{resume_id}/claims`

可选 Query：`revision_id`。

预期返回：

```json
{
  "resume_id": "res_xxx",
  "claims": [
    {
      "claim_id": "clm_xxx",
      "priority": 82,
      "confidence": 0.88,
      "disabled": false,
      "data": {
        "claim_id": "clm_xxx",
        "entry_id": "entry_xxx",
        "claim_text": "...",
        "verification_points": []
      },
      "created_at": "2026-07-27T10:10:00"
    }
  ]
}
```

接口会通过 `select_core_claims` 返回有限的面试价值较高 Claim 集合。

### PATCH `/resumes/{resume_id}/claims/{claim_id}`

请求字段均可选：

```json
{
  "enabled": true,
  "priority": 90
}
```

Priority 范围 0–100。

预期返回：

```json
{
  "claim_id": "clm_xxx",
  "resume_id": "res_xxx",
  "priority": 90,
  "disabled": false
}
```

### PATCH `/resumes/{resume_id}/target-role`

保存或修改简历绑定的目标岗位，并让主张按新岗位重新排序（保留手动禁用的主张）。

请求：

```json
{
  "target_role": "高级后端工程师",
  "job_target_id": "jt_xxx"
}
```

预期返回：

```json
{
  "resume_id": "res_xxx",
  "target_role": "高级后端工程师",
  "job_target_id": "jt_xxx",
  "message": "目标岗位已保存，主张已按新岗位重新排序"
}
```

### GET `/resumes/{resume_id}/revisions`

返回该简历的 Revision 历史，按创建时间倒序：

```json
{
  "resume_id": "res_xxx",
  "revisions": [
    {
      "revision_id": "rev_xxx",
      "status": "CONFIRMED",
      "extraction_quality": 0.95,
      "created_at": "2026-07-27T10:00:00"
    }
  ]
}
```

不存在的简历返回 404。

### DELETE `/resumes/{resume_id}`

删除简历及关联 Revision、Blocks、Profile、Claims、Interviews、Questions、Answers 和 Reports。

```json
{
  "resume_id": "res_xxx",
  "status": "deleted"
}
```

该操作不可恢复，调用前应由 UI 二次确认。

## 6. 面试接口

### GET `/interviews`

Query：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `page` | 1 | 页码 |
| `page_size` | 20 | 每页 1–100 |
| `status` | null | `in_progress` / `finished` |
| `mode` | null | `simulation` / `practice` |
| `resume_id` | null | 按简历筛选 |
| `sort_by` | `created_at` | 创建时间或状态 |
| `sort_order` | `desc` | 排序方向 |

预期返回：

```json
{
  "items": [
    {
      "interview_id": "iv_xxx",
      "thread_id": "thread_xxx",
      "resume_id": "res_xxx",
      "target_role": "高级后端工程师",
      "mode": "simulation",
      "max_turns": 20,
      "status": "in_progress",
      "turn_count": 4,
      "finished": false,
      "created_at": "2026-07-27T11:00:00",
      "finished_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

`turn_count` 取 Graph State 和数据库已保存 Answer 数量的较大值。

### POST `/interviews`

请求：

```json
{
  "resume_id": "res_xxx",
  "resume_revision_id": "rev_xxx",
  "target_role": "高级后端工程师",
  "job_description": "负责高并发服务和数据平台...",
  "job_target_id": "jt_xxx",
  "mode": "simulation",
  "max_turns": 20,
  "model_tier": "auto"
}
```

前置条件：

- Revision 存在。
- Revision 状态为 `CONFIRMED`。
- Profile 和 Claims 已生成。

`mode` 取值 `simulation`（模拟面试）/ `practice`（练习模式）；`model_tier` 取值 `auto` / `fast` / `balanced` / `judge`。

接口会立即运行 Graph 到第一处 Interrupt，并保存第一题。

预期返回：

```json
{
  "interview_id": "iv_xxx",
  "thread_id": "thread_xxx",
  "status": "in_progress",
  "current_question": "请介绍这个项目的目标、整体架构以及你负责的部分。",
  "question_id": "q_xxx",
  "turn_count": 0,
  "max_turns": 20
}
```

### GET `/interviews/{interview_id}`

预期返回：

```json
{
  "interview_id": "iv_xxx",
  "thread_id": "thread_xxx",
  "resume_id": "res_xxx",
  "target_role": "高级后端工程师",
  "mode": "simulation",
  "status": "in_progress",
  "turn_count": 1,
  "max_turns": 20,
  "current_question": {
    "question_id": "q_002",
    "question_text": "失败重试时如何保证幂等？",
    "topic_id": "topic_xxx",
    "claim_id": "clm_xxx",
    "verification_point_id": "vp_xxx",
    "depth": 4
  },
  "finished": false,
  "stop_reason": "CONTINUE_DEEPENING",
  "history": [
    {
      "question_id": "q_001",
      "question_text": "请介绍项目整体架构。",
      "answer_text": "项目分为...",
      "evaluation": {
        "dimensions": [],
        "strengths": [],
        "key_missing_points": []
      },
      "analysis": {},
      "coaching": {
        "what_was_good": [],
        "what_to_improve": [],
        "expert_answer": ""
      }
    }
  ]
}
```

History 会从持久化 Questions 和 Answers 进行兜底重建。

### POST `/interviews/{interview_id}/answers`

请求：

```json
{
  "question_id": "q_002",
  "answer_text": "我们使用业务幂等键和唯一索引...",
  "idempotency_key": "iv_xxx_q_002_550e8400-e29b-41d4-a716-446655440000"
}
```

处理：

1. 验证 Interview 未结束。
2. 按 `idempotency_key` 检查重复提交。
3. 验证 `question_id` 是当前问题。
4. 发布 `answer.accepted`。
5. 恢复 Graph，完成分析、评分、证据更新、Coaching 和 Decision。
6. 保存 Answer、下一题或 Report。
7. 发布对应 SSE 事件。

预期返回：

```json
{
  "interview_id": "iv_xxx",
  "status": "in_progress",
  "turn_count": 2,
  "current_question": {
    "question_id": "q_003",
    "question_text": "如果数据库写成功但消息发送失败，你如何恢复？",
    "depth": 5
  },
  "next_question": "如果数据库写成功但消息发送失败，你如何恢复？",
  "next_question_id": "q_003",
  "analysis": {
    "answer_summary": "候选人使用幂等键和唯一索引...",
    "addressed_expected_points": ["业务幂等键"],
    "partially_addressed_points": ["失败恢复"],
    "missing_expected_points": ["事务边界"],
    "answer_relevance": 0.95,
    "information_density": 0.78,
    "follow_up_value": 0.82
  },
  "evaluation": {
    "dimensions": [
      {
        "dimension": "implementation_depth",
        "score": 72,
        "max_score": 100,
        "reason": "说明了幂等键和唯一索引，但恢复链路不完整。",
        "answer_evidence": ["业务幂等键", "唯一索引"],
        "missing_points": ["事务边界"],
        "confidence": 0.86
      }
    ],
    "strengths": ["给出了具体实现手段"],
    "factual_errors": [],
    "unsupported_claims": [],
    "key_missing_points": ["数据库与消息的一致性"],
    "demonstrated_level": "intermediate",
    "evaluation_confidence": 0.86,
    "model_recommended_action": "follow_up",
    "model_recommended_depth": 5
  },
  "coaching": {
    "score_summary": "实现思路基本正确，但异常链路不完整。",
    "question_analysis": "问题考察幂等、事务边界和失败恢复。",
    "what_was_good": ["提到了业务幂等键"],
    "what_to_improve": ["补充消息发送失败后的恢复机制"],
    "expert_answer": "一份强回答会先定义幂等边界...",
    "answer_framework": ["定义问题", "说明约束", "给出方案", "覆盖失败场景"],
    "likely_follow_up_questions": ["如何处理幂等记录过期？"],
    "knowledge_gaps": ["事务消息"]
  },
  "finished": false
}
```

若重复幂等键已保存，预期返回：

```json
{
  "interview_id": "iv_xxx",
  "status": "in_progress",
  "duplicate": true
}
```

若 Question ID 不匹配返回 400。

### POST `/interviews/{interview_id}/finish`

主动结束。Graph 使用特殊的 `[END OF INTERVIEW]` Resume Command，但报告统计会排除这条占位回答。

预期返回：

```json
{
  "interview_id": "iv_xxx",
  "status": "finished",
  "has_report": true
}
```

若已经结束：

```json
{
  "interview_id": "iv_xxx",
  "status": "finished"
}
```

## 7. SSE 事件接口

### GET `/interviews/{interview_id}/events`

Headers：

```http
Accept: text/event-stream
```

响应头：

```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

连接建立时先发送：

```text
:ok
```

无事件 15 秒发送：

```text
:heartbeat
```

业务事件：

```text
data: {"event_id":"...","event_type":"question.ready",...}
```

统一 Envelope：

```json
{
  "event_id": "16-char-id",
  "event_type": "question.ready",
  "interview_id": "iv_xxx",
  "thread_id": "thread_xxx",
  "sequence": 3,
  "created_at": "2026-07-27T11:01:00",
  "payload": {}
}
```

事件类型：

| Event | Payload 关键字段 | 含义 |
| --- | --- | --- |
| `interview.initialized` | `interview_id`, `target_role`, `mode` | Graph 和第一题上下文已初始化 |
| `question.ready` | `question_id`, `question_text`, 可选 `turn_count` | 新问题可作答 |
| `answer.accepted` | `question_id` | 回答已接收，开始处理 |
| `analysis.completed` | `question_id`, `analysis` | 分析完成 |
| `scoring.completed` | `question_id`, `evaluation` | 六维评分完成 |
| `coaching.ready` | `question_id`, `coaching` | 教练反馈和强回答示例完成 |
| `interview.finished` | `stop_reason`, `turn_count` | 面试结束 |
| `report.ready` | `{}` | 报告已保存 |

晚加入或重连的客户端会收到当前状态 Snapshot：

- 未结束：`interview.initialized` + `question.ready`。
- 已结束：`interview.finished`。

## 8. 报告接口

### GET `/interviews/{interview_id}/report`

报告未生成：

```json
{
  "interview_id": "iv_xxx",
  "report": null,
  "status": "in_progress"
}
```

报告已生成：

```json
{
  "interview_id": "iv_xxx",
  "created_at": "2026-07-27T12:00:00",
  "report": {
    "report_text": "自然语言报告...",
    "interview_id": "iv_xxx",
    "summary": {
      "overall_score": 76.4,
      "total_questions": 12,
      "questions_asked": 12,
      "questions_answered": 11,
      "claims_verified": 3,
      "contradictions_found": 1
    },
    "ability_scores": {
      "technical_correctness": 80.0,
      "implementation_depth": 72.0
    },
    "claim_statuses": {},
    "question_details": [],
    "contradictions": [],
    "coverage": {}
  }
}
```

接口会使用数据库 Questions/Answers 为旧报告补齐逐题详情、能力分和 Summary。

### POST `/interviews/{interview_id}/report/export`

请求：

```json
{
  "format": "markdown"
}
```

- `markdown`：返回 `text/markdown`。
- 其他值：返回报告 JSON。

Markdown 当前是基础导出，包含总分、总结、能力、正文和建议。

## 9. 岗位目标接口

### GET `/job-targets`

返回当前用户的全部岗位目标：

```json
[
  {
    "job_target_id": "jt_xxx",
    "title": "Java 后端工程师",
    "level": "mid",
    "interview_round": "technical",
    "description": "Java + Spring Boot 后端开发",
    "source": "template",
    "raw_jd": null,
    "requirements": [
      {
        "requirement_id": "req_xxx",
        "competency_code": "backend.language_runtime",
        "title": "Java 语言与 JVM",
        "description": "掌握 Java 核心特性与 JVM 调优",
        "importance": 0.9,
        "expected_level": 3,
        "evidence_expectation": ["能说明 JVM 内存模型", "能分析线程安全问题"]
      }
    ],
    "created_at": "2026-08-01T10:00:00"
  }
]
```

### POST `/job-targets`

请求：

```json
{
  "title": "Java 后端工程师",
  "level": "mid",
  "interview_round": "technical",
  "description": "Java + Spring Boot 后端开发",
  "source": "manual",
  "requirements": [
    {
      "competency_code": "backend.language_runtime",
      "title": "Java 语言与 JVM",
      "importance": 0.9,
      "expected_level": 3,
      "evidence_expectation": ["能说明 JVM 内存模型", "能分析线程安全问题"]
    }
  ]
}
```

`source` 取值 `template` / `pasted_jd` / `manual`；`level` 取值 `intern` / `junior` / `mid` / `senior` / `staff`；`interview_round` 取值 `resume` / `project` / `technical` / `system_design`。返回 201 与完整岗位对象。

### POST `/job-targets/parse-jd`

请求：

```json
{
  "jd_text": "负责高并发服务的后端开发，要求熟练掌握 Java、Spring Boot 和 MySQL..."
}
```

预期返回：

```json
{
  "requirements": [
    {
      "competency_code": "backend.language_runtime",
      "title": "Java 语言与 JVM",
      "importance": 0.9,
      "expected_level": 3,
      "evidence_expectation": ["能说明 JVM 内存模型", "能进行性能调优"]
    }
  ],
  "inferred_level": "mid",
  "inferred_round": "technical"
}
```

### GET `/job-targets/{job_target_id}` / PATCH `/job-targets/{job_target_id}`

详情返回同 `GET /job-targets` 单项；PATCH 支持部分更新（不可将 `title` / `level` / `interview_round` / `source` 显式置空）。模板创建的岗位名称在 UI 中锁定为只读。

## 10. 能力缺口分析接口

### POST `/claim-gap`

请求：

```json
{
  "resume_id": "res_xxx",
  "job_target_id": "jt_xxx"
}
```

触发（或复用已缓存结果的）缺口分析。预期返回：

```json
{
  "resume_id": "res_xxx",
  "job_target_id": "jt_xxx",
  "gaps": [
    {
      "gap_type": "UNCOVERED_REQUIREMENT",
      "claim_id": null,
      "requirement_id": "req_xxx",
      "competency_code": "backend.cache",
      "priority": 0.88,
      "reason_codes": ["no_matching_claim"],
      "explanation": "岗位要求缓存设计能力，简历中没有对应主张",
      "claim_text": null,
      "requirement_title": "缓存设计",
      "requirement_importance": 0.85,
      "requirement_expected_level": 3,
      "claim_coverage_level": 0
    }
  ],
  "coverage_stats": {
    "total_requirements": 5,
    "covered_requirements": 3,
    "uncovered_requirements": 1,
    "weak_evidence_count": 1,
    "high_priority_gaps": 1,
    "coverage_percentage": 60.0
  },
  "interview_plan": {},
  "high_priority_targets": ["backend.cache"]
}
```

`gap_type` 取值 `UNCOVERED_REQUIREMENT` / `WEAK_EVIDENCE` / `CONTRADICTED_CLAIM`。

### GET `/claim-gap/resume/{resume_id}/job-target/{job_target_id}`

获取已保存的缺口分析结果，结构同上；未分析时返回空结果。

## 11. 证据接口

### GET `/evidence/verification-points/{claim_id}`

返回主张下的验证点及当前证据状态：

```json
{
  "claim_id": "clm_xxx",
  "verification_points": [
    {
      "verification_point_id": "vp_xxx",
      "claim_id": "clm_xxx",
      "competency_code": "backend.language_runtime",
      "aspect": "线程安全分析",
      "current_state": "VERIFIED",
      "strength": 0.82,
      "confidence": "high",
      "evidence_count": 3,
      "transition_count": 2,
      "has_contradictions": false,
      "created_at": "2026-08-01T10:00:00",
      "updated_at": "2026-08-03T12:00:00"
    }
  ]
}
```

证据状态取值 `UNSEEN` / `ADDRESSED` / `PARTIALLY_SUPPORTED` / `VERIFIED`。

### GET `/evidence/transitions/{verification_point_id}`

返回验证点状态迁移历史，每条含 `from_state` / `to_state` / `reason_code` / `answer_id` / `evidence_spans` / `policy_version`。

### GET `/evidence/contradictions/{interview_id}`

返回该面试中的矛盾记录（`contradiction_type` / `severity` / `clarification_question` / `conflicting_answers` / `resolution_status`）。

### GET `/evidence/evidence/{verification_point_id}`

返回验证点的证据片段列表（`start` / `end` / `text` / `quote_hash`）。

## 12. 能力档案接口

### GET `/abilities/profile/{resume_id}`

聚合该简历在已完成的面试中的能力表现：

```json
{
  "resume_id": "res_xxx",
  "total_interviews": 3,
  "competencies": [
    {
      "competency_code": "technical_correctness",
      "profile": {
        "average_score": 78.5,
        "stability": "MEDIUM",
        "sample_size": 3,
        "trend": "stable",
        "transfer_status": "VERIFIED"
      },
      "history": [
        { "interview_id": "iv_001", "score": 75.0, "date": "2026-08-01" },
        { "interview_id": "iv_002", "score": 82.0, "date": "2026-08-03" }
      ]
    }
  ]
}
```

`stability` 取值 `LOW` / `MEDIUM` / `HIGH`。

## 13. 训练计划接口

### GET `/training-plans`

可选 Query：`resume_id`。返回当前用户的训练任务，按优先级倒序：

```json
[
  {
    "task_id": "tp_xxx",
    "task_type": "EVIDENCE_COMPLETION",
    "competency_code": "technical_correctness",
    "title": "补充并发场景证据",
    "description": "针对 Java 并发主张补充可验证的线上案例",
    "completion_criteria": ["能复述线程池参数配置", "能给出一次线上调优记录"],
    "status": "PENDING",
    "priority": 0.9,
    "resume_id": "res_xxx",
    "interview_id": null,
    "created_at": "2026-08-04T10:00:00",
    "completed_at": null
  }
]
```

`task_type` 取值 `EVIDENCE_COMPLETION` / `CONCEPT_REVIEW` / `DEPTH_IMPROVEMENT` / `CONTRADICTION_RESOLUTION` / `FORM_DIVERSIFICATION` / `TRANSFER_PRACTICE`。

### POST `/training-plans/{resume_id}/generate`

按简历的证据缺口与能力短板生成训练任务。

### PATCH `/training-plans/{task_id}`

请求：

```json
{
  "status": "COMPLETED"
}
```

状态取值 `PENDING` / `IN_PROGRESS` / `COMPLETED` / `DISMISSED`。

## 14. Dashboard 与 Analytics

### GET `/dashboard/summary`

```json
{
  "total_resumes": 8,
  "total_interviews": 15,
  "pending_reviews": 1,
  "completed_interviews": 12,
  "in_progress_count": 3,
  "average_score": 75.6,
  "recent_resumes": [],
  "in_progress_interviews": []
}
```

### GET `/analytics/summary`

```json
{
  "total_interviews": 15,
  "average_score": 75.6,
  "score_distribution": {
    "0-20": 0,
    "21-40": 1,
    "41-60": 2,
    "61-80": 7,
    "81-100": 2
  },
  "top_abilities": [
    {"name": "technical_correctness", "score": 82.0}
  ],
  "weak_abilities": [
    {"name": "production_awareness", "score": 61.5}
  ],
  "claim_verification_rate": 68.4,
  "claim_status_counts": {
    "VERIFIED": 13,
    "PARTIALLY_VERIFIED": 5,
    "IN_PROGRESS": 1
  }
}
```

### GET `/analytics/trends`

```json
{
  "interviews_over_time": [
    {"week": "2026-W29", "count": 4},
    {"week": "2026-W30", "count": 6}
  ],
  "score_trend": [
    {"date": "2026-07-25", "score": 74.5},
    {"date": "2026-07-27", "score": 81.0}
  ]
}
```

## 15. 客户端调用顺序

推荐端到端调用：

```text
POST /register 或 POST /login（获取 access_token）
  -> POST /resumes
  -> PATCH revision（可选）
  -> POST revision/confirm
  -> GET claims
  -> PATCH claim（可选）
  -> POST /job-targets（可选，或 /job-targets/parse-jd）
  -> POST /claim-gap（可选，缺口分析）
  -> POST /interviews（携带 job_target_id / model_tier）
  -> GET /interviews/{id}/events
  -> POST /interviews/{id}/answers（循环）
  -> GET /interviews/{id}（恢复/轮询）
  -> GET /interviews/{id}/report
  -> GET /abilities/profile/{resume_id} / POST /training-plans/{resume_id}/generate（面试后分析）
```

除 `/register`、`/login`、`/health` 外，所有请求需携带 `Authorization: Bearer <access_token>`。
