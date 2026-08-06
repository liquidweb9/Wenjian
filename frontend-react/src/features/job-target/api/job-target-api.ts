import { api } from "@/lib/api-client"
import type {
  JobTarget,
  JobTargetCreateRequest,
  ParseJDRequest,
  ParseJDResponse,
  RequirementUpdateRequest,
  JobTargetTemplate,
} from "@/lib/types/job-target"

/**
 * Job Target API layer
 */
export const jobTargetApi = {
  /**
   * List all job targets for current user
   */
  async list(): Promise<JobTarget[]> {
    const response = await api.get<JobTarget[]>("/job-targets")
    return response.data
  },

  /**
   * Get a specific job target by ID
   */
  async get(jobTargetId: string): Promise<JobTarget> {
    const response = await api.get<JobTarget>(`/job-targets/${jobTargetId}`)
    return response.data
  },

  /**
   * Create a new job target
   */
  async create(data: JobTargetCreateRequest): Promise<JobTarget> {
    const response = await api.post<JobTarget>("/job-targets", data)
    return response.data
  },

  /**
   * Update a job target
   */
  async update(jobTargetId: string, data: Partial<JobTargetCreateRequest>): Promise<JobTarget> {
    const response = await api.patch<JobTarget>(`/job-targets/${jobTargetId}`, data)
    return response.data
  },

  /**
   * Delete a job target
   */
  async delete(jobTargetId: string): Promise<void> {
    await api.delete(`/job-targets/${jobTargetId}`)
  },

  /**
   * Parse JD text into structured requirements
   */
  async parseJD(data: ParseJDRequest): Promise<ParseJDResponse> {
    const response = await api.post<ParseJDResponse>("/job-targets/parse-jd", data)
    return response.data
  },

  /**
   * Update a specific requirement
   */
  async updateRequirement(
    jobTargetId: string,
    requirementId: string,
    data: RequirementUpdateRequest,
  ): Promise<void> {
    await api.patch(`/job-targets/${jobTargetId}/requirements/${requirementId}`, data)
  },

  /**
   * Get predefined job target templates
   */
  getTemplates(): JobTargetTemplate[] {
    return JOB_TARGET_TEMPLATES
  },
}

/**
 * Predefined job target templates
 */
const JOB_TARGET_TEMPLATES: JobTargetTemplate[] = [
  {
    id: "java-backend",
    title: "Java 后端工程师",
    level: "mid",
    description: "Java + Spring Boot 后端开发，熟悉分布式系统和微服务架构",
    requirements: [
      {
        competency_code: "backend.language_runtime",
        title: "Java 语言与 JVM",
        description: "掌握 Java 核心特性、并发、内存模型和 JVM 调优",
        importance: 0.9,
        expected_level: 3,
        evidence_expectation: ["能说明 JVM 内存模型", "能分析线程安全问题", "能进行性能调优"],
      },
      {
        competency_code: "backend.api_protocol",
        title: "REST API 设计",
        description: "设计和实现 RESTful API，处理请求响应",
        importance: 0.85,
        expected_level: 3,
        evidence_expectation: ["能设计资源端点", "能处理错误响应", "能说明幂等性"],
      },
      {
        competency_code: "backend.database_modeling",
        title: "数据库建模",
        description: "MySQL/PostgreSQL 表设计、索引优化、查询调优",
        importance: 0.8,
        expected_level: 3,
        evidence_expectation: ["能设计表结构", "能优化慢查询", "能说明索引策略"],
      },
      {
        competency_code: "backend.cache",
        title: "缓存设计",
        description: "Redis 缓存方案、一致性处理、性能优化",
        importance: 0.85,
        expected_level: 3,
        evidence_expectation: ["能说明缓存模式", "能分析一致性风险", "能说明监控与故障处理"],
      },
      {
        competency_code: "backend.message_queue",
        title: "消息队列",
        description: "Kafka/RabbitMQ 消息处理、重试、幂等",
        importance: 0.75,
        expected_level: 2,
        evidence_expectation: ["能说明消息模型", "能处理消费失败"],
      },
    ],
  },
  {
    id: "go-backend",
    title: "Go 后端工程师",
    level: "mid",
    description: "Go 语言后端开发，熟悉高并发和分布式系统",
    requirements: [
      {
        competency_code: "backend.language_runtime",
        title: "Go 语言特性",
        description: "掌握 Go 核心特性、goroutine、channel、内存管理",
        importance: 0.9,
        expected_level: 3,
        evidence_expectation: ["能说明 goroutine 调度", "能分析 channel 使用", "能处理并发安全"],
      },
      {
        competency_code: "backend.concurrency",
        title: "并发处理",
        description: "高并发场景下的协程管理、锁机制、性能优化",
        importance: 0.85,
        expected_level: 3,
        evidence_expectation: ["能设计并发方案", "能避免死锁", "能分析性能瓶颈"],
      },
      {
        competency_code: "backend.api_protocol",
        title: "API 开发",
        description: "gRPC/HTTP API 设计与实现",
        importance: 0.8,
        expected_level: 3,
        evidence_expectation: ["能设计 API 接口", "能处理错误", "能说明性能优化"],
      },
    ],
  },
  {
    id: "python-backend",
    title: "Python 后端工程师",
    level: "mid",
    description: "Python FastAPI/Django 后端开发",
    requirements: [
      {
        competency_code: "backend.language_runtime",
        title: "Python 语言特性",
        description: "掌握 Python 核心特性、异步编程、类型系统",
        importance: 0.85,
        expected_level: 3,
        evidence_expectation: ["能使用 async/await", "能说明类型注解", "能处理异常"],
      },
      {
        competency_code: "backend.api_protocol",
        title: "FastAPI 开发",
        description: "FastAPI 路由、依赖注入、数据验证",
        importance: 0.9,
        expected_level: 3,
        evidence_expectation: ["能设计路由", "能使用 Pydantic", "能处理中间件"],
      },
      {
        competency_code: "backend.database_modeling",
        title: "ORM 与数据库",
        description: "SQLAlchemy ORM、查询优化、事务管理",
        importance: 0.8,
        expected_level: 3,
        evidence_expectation: ["能设计模型", "能优化查询", "能处理事务"],
      },
    ],
  },
  {
    id: "ai-agent-engineer",
    title: "AI Agent 应用工程师",
    level: "mid",
    description: "LangChain/LangGraph Agent 应用开发",
    requirements: [
      {
        competency_code: "agent.prompt_design",
        title: "Prompt 工程",
        description: "设计高质量 Prompt、Few-shot、思维链",
        importance: 0.9,
        expected_level: 3,
        evidence_expectation: ["能设计有效 Prompt", "能处理边界情况", "能优化输出质量"],
      },
      {
        competency_code: "agent.structured_output",
        title: "结构化输出",
        description: "JSON Schema 约束、输出验证、错误处理",
        importance: 0.85,
        expected_level: 3,
        evidence_expectation: ["能定义输出格式", "能处理解析错误", "能验证输出"],
      },
      {
        competency_code: "agent.workflow_orchestration",
        title: "工作流编排",
        description: "LangGraph 状态机、节点设计、路由策略",
        importance: 0.9,
        expected_level: 3,
        evidence_expectation: ["能设计状态图", "能实现条件路由", "能处理错误恢复"],
      },
      {
        competency_code: "agent.tool_calling",
        title: "Tool Calling",
        description: "工具调用、参数校验、结果处理",
        importance: 0.8,
        expected_level: 3,
        evidence_expectation: ["能定义工具", "能处理调用", "能验证参数"],
      },
      {
        competency_code: "agent.eval",
        title: "Eval 与测试",
        description: "Golden Dataset、回归测试、指标监控",
        importance: 0.75,
        expected_level: 2,
        evidence_expectation: ["能建立测试集", "能运行回归", "能分析指标"],
      },
    ],
  },
  {
    id: "backend-intern",
    title: "后端实习生",
    level: "intern",
    description: "后端开发实习，学习基础技能",
    requirements: [
      {
        competency_code: "backend.language_runtime",
        title: "编程语言基础",
        description: "掌握一门后端语言的基本语法和特性",
        importance: 0.9,
        expected_level: 2,
        evidence_expectation: ["能写基本逻辑", "能使用标准库"],
      },
      {
        competency_code: "backend.api_protocol",
        title: "API 基础",
        description: "了解 HTTP 协议、REST API 基本概念",
        importance: 0.8,
        expected_level: 2,
        evidence_expectation: ["能说明 HTTP 方法", "能理解状态码"],
      },
      {
        competency_code: "backend.database_modeling",
        title: "数据库基础",
        description: "SQL 基本查询、表结构理解",
        importance: 0.75,
        expected_level: 2,
        evidence_expectation: ["能写基本查询", "能理解主外键"],
      },
    ],
  },
]
