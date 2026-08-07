import { useState, useRef } from "react"
import { useUploadResumeFile, useUploadResumeText } from "../hooks/use-resumes"
import { getResumeErrorMessage } from "../utils/error-mapping"
import { ApiError } from "@/lib/api-client"
import { PageHeader } from "@/components/common/page-header"
import { usePageTitle } from "@/lib/use-page-title"

const ALLOWED_EXTENSIONS = [".pdf", ".txt", ".tex"]
const MAX_SIZE_MB = 5
const MAX_SIZE = MAX_SIZE_MB * 1024 * 1024

export default function ResumeUploadPage() {
  usePageTitle("", "上传简历")
  const [tab, setTab] = useState<"file" | "text">("file")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [textInput, setTextInput] = useState("")
  const [fileName, setFileName] = useState("")
  const [validationError, setValidationError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fileMutation = useUploadResumeFile()
  const textMutation = useUploadResumeText()

  function validateFile(file: File): string | null {
    const ext = "." + file.name.split(".").pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `不支持的文件类型。仅支持 ${ALLOWED_EXTENSIONS.join(", ")}`
    }
    if (file.size > MAX_SIZE) {
      return `文件大小不能超过 ${MAX_SIZE_MB} MB`
    }
    if (file.size === 0) {
      return "文件为空"
    }
    return null
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setValidationError(null)
    setSelectedFile(file)
    const err = validateFile(file)
    if (err) {
      setValidationError(err)
      setSelectedFile(null)
    }
  }

  async function handleFileUpload() {
    if (!selectedFile) return
    setValidationError(null)
    try {
      await fileMutation.mutateAsync(selectedFile)
    } catch (e) {
      if (e instanceof ApiError) {
        setValidationError(getResumeErrorMessage(e.code))
      } else {
        setValidationError("上传失败，请重试")
      }
    }
  }

  async function handleTextUpload() {
    if (!textInput.trim()) {
      setValidationError("请输入简历内容")
      return
    }
    if (!fileName.trim()) {
      setValidationError("请输入文件名")
      return
    }
    setValidationError(null)
    try {
      await textMutation.mutateAsync({ fileName: fileName.trim(), text: textInput })
    } catch (e) {
      if (e instanceof ApiError) {
        setValidationError(getResumeErrorMessage(e.code))
      } else {
        setValidationError("提交失败，请重试")
      }
    }
  }

  const isUploading = fileMutation.isPending || textMutation.isPending

  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <PageHeader
        title="上传简历"
        description="支持 PDF、TXT、TEX 格式，上传后问鉴会自动解析提取关键信息。"
        brand
        back={{ to: "/app/resumes", label: "返回简历管理" }}
      />

      {/* Tab switcher */}
      <div style={{ display: "flex", gap: 0, marginBottom: "1.5rem" }}>
        <button
          onClick={() => { setTab("file"); setValidationError(null) }}
          style={{
            padding: "0.5rem 1.2rem",
            border: "1px solid #e2e8f0",
            borderRadius: "6px 0 0 6px",
            backgroundColor: tab === "file" ? "#0d1b2a" : "#fff",
            color: tab === "file" ? "#fff" : "#333",
          }}
        >
          上传文件
        </button>
        <button
          onClick={() => { setTab("text"); setValidationError(null) }}
          style={{
            padding: "0.5rem 1.2rem",
            border: "1px solid #e2e8f0",
            borderRadius: "0 6px 6px 0",
            backgroundColor: tab === "text" ? "#0d1b2a" : "#fff",
            color: tab === "text" ? "#fff" : "#333",
          }}
        >
          粘贴文本
        </button>
      </div>

      {/* Validation / upload error */}
      {validationError && (
        <div
          style={{
            padding: "0.75rem 1rem",
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "8px",
            color: "#e63946",
            fontSize: "0.9rem",
            marginBottom: "1rem",
          }}
        >
          {validationError}
        </div>
      )}

      {fileMutation.error && !validationError && (
        <div
          style={{
            padding: "0.75rem 1rem",
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "8px",
            color: "#e63946",
            fontSize: "0.9rem",
            marginBottom: "1rem",
          }}
        >
          {fileMutation.error instanceof ApiError
            ? getResumeErrorMessage(fileMutation.error.code)
            : "上传失败"}
        </div>
      )}

      <div
        style={{
          backgroundColor: "#fff",
          borderRadius: "12px",
          border: "1px solid #e2e8f0",
          padding: "2rem",
        }}
      >
        {tab === "file" ? (
          <div>
            {/* Drop zone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${selectedFile ? "#22c55e" : "#e2e8f0"}`,
                borderRadius: "8px",
                padding: "2.5rem 2rem",
                textAlign: "center",
                cursor: "pointer",
                backgroundColor: selectedFile ? "#f0fdf4" : "#fafafa",
              }}
            >
              {selectedFile ? (
                <div>
                  <div style={{ fontSize: "1rem", fontWeight: 500 }}>{selectedFile.name}</div>
                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.25rem" }}>
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ color: "#64748b" }}>
                    点击选择文件，或拖拽文件到此处
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.5rem" }}>
                    支持 PDF、TXT、TEX 格式 (最大 {MAX_SIZE_MB}MB)
                  </div>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.tex"
                onChange={handleFileChange}
                style={{ display: "none" }}
              />
            </div>
            <button
              onClick={handleFileUpload}
              disabled={!selectedFile || isUploading}
              style={{
                marginTop: "1rem",
                width: "100%",
                padding: "0.6rem 1.5rem",
                backgroundColor: !selectedFile || isUploading ? "#cbd5e1" : "#0d1b2a",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontSize: "1rem",
              }}
            >
              {isUploading ? "上传中..." : "上传"}
            </button>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: "0.75rem" }}>
              <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 500, marginBottom: "0.25rem" }}>
                文件名
              </label>
              <input
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="例如：张三_简历.txt"
                style={{
                  width: "100%",
                  padding: "0.5rem 0.75rem",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                  fontSize: "0.9rem",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 500, marginBottom: "0.25rem" }}>
                简历内容
              </label>
              <textarea
                rows={12}
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="在此粘贴你的简历内容..."
                style={{
                  width: "100%",
                  padding: "0.75rem",
                  border: "1px solid #e2e8f0",
                  borderRadius: "6px",
                  resize: "vertical",
                  fontSize: "0.9rem",
                }}
              />
            </div>
            <button
              onClick={handleTextUpload}
              disabled={isUploading}
              style={{
                marginTop: "1rem",
                width: "100%",
                padding: "0.6rem 1.5rem",
                backgroundColor: isUploading ? "#cbd5e1" : "#0d1b2a",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontSize: "1rem",
              }}
            >
              {isUploading ? "提交中..." : "提交"}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
