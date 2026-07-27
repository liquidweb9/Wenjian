const resumeErrorMessages: Record<string, string> = {
  RESUME_EMPTY: "文件内容为空，请重新选择。",
  RESUME_TOO_LARGE: "文件超过 5 MB 限制。",
  RESUME_UNSUPPORTED_TYPE: "仅支持 PDF、TXT 和单文件 TEX。",
  RESUME_TYPE_MISMATCH: "文件扩展名与实际内容不一致。",
  PDF_ENCRYPTED: "暂不支持加密 PDF。",
  PDF_NO_TEXT: "未检测到可提取文本，请上传文本型 PDF 或粘贴文本。",
  PDF_TOO_MANY_PAGES: "PDF 页数超过限制。",
  LATEX_MULTI_FILE_NOT_SUPPORTED: "不支持多文件 LaTeX 工程。",
  LATEX_PARSE_FAILED: "LaTeX 解析失败，请检查文件格式。",
  PARSE_QUALITY_TOO_LOW: "解析质量过低，请修改内容或更换文件。",
}

export function getResumeErrorMessage(code: string): string {
  return resumeErrorMessages[code] ?? `未知错误 (${code})`
}
