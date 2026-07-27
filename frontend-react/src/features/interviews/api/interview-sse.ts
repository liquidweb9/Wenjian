export type SSECallback = (event: Record<string, unknown>) => void

export function createSSEConnection(
  interviewId: string,
  onEvent: SSECallback,
  onConnectionChange: (state: string) => void,
  signal: AbortSignal,
): () => void {
  let retries = 0
  let aborted = false
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  const maxRetries = 10

  async function connect() {
    if (aborted) return
    onConnectionChange(retries === 0 ? "connecting" : "reconnecting")

    try {
      const response = await fetch(`/api/v1/interviews/${interviewId}/events`, {
        headers: { Accept: "text/event-stream" },
        signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }

      onConnectionChange("connected")
      retries = 0

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6))
              onEvent(event)
            } catch {
              // skip heartbeat comments
            }
          }
        }
      }

      // Stream ended naturally — reconnect
      scheduleReconnect()
    } catch (e) {
      if ((e as Error).name === "AbortError") return
      onConnectionChange("disconnected")
      scheduleReconnect()
    }
  }

  function scheduleReconnect() {
    if (aborted || retries >= maxRetries) {
      onConnectionChange("failed")
      return
    }
    const delay = Math.min(1000 * Math.pow(2, retries), 15000)
    retries++
    timeoutId = setTimeout(connect, delay)
  }

  connect()

  return () => {
    aborted = true
    if (timeoutId) clearTimeout(timeoutId)
  }
}
