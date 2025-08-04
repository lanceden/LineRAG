"use client"

import { useState, useRef, useEffect } from "react"

interface Message {
  id: string
  role: "user" | "assistant"
  parts: { type: "text"; text: string }[]
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const sendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      parts: [{ type: "text", text }],
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    // 預先建立一個空的 assistant 訊息，準備即時更新
    const assistantId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      parts: [{ type: "text", text: "" }],
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage],
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantText = ""

      if (reader) {
        setIsLoading(false)
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split("\n")

          for (const line of lines) {
            if (line.startsWith("data: ") && line !== "data: [DONE]") {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === "text") {
                  assistantText += data.text // 累積字符

                  // 即時更新 assistant 訊息
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantId
                        ? {
                            ...msg,
                            parts: [{ type: "text", text: assistantText }],
                          }
                        : msg
                    )
                  )
                }
              } catch (e) {
                console.error("Failed to parse JSON:", e)
              }
            }
          }
        }
      }

      // 如果沒有收到任何內容，顯示錯誤訊息
      if (!assistantText) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, parts: [{ type: "text", text: "回覆失敗" }] }
              : msg
          )
        )
      }
    } catch (error) {
      console.error("Error sending message:", error)
      // 更新 assistant 訊息為錯誤訊息
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                parts: [
                  { type: "text", text: "發送訊息時發生錯誤，請稍後再試" },
                ],
              }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      sendMessage(input.trim())
      setInput("")
    }
  }

  return (
    <div className="max-w-xl mx-auto p-4">
      <div className="space-y-2 mb-4 h-[60vh] overflow-y-auto border rounded p-2">
        {messages.map((m) => (
          <div
            key={m.id}
            className={m.role === "user" ? "text-right" : "text-left"}>
            <div className="inline-block bg-gray-100 px-3 py-1 rounded">
              {m.parts.map((part, index) =>
                part.type === "text" ? (
                  <span key={index} className="whitespace-pre-wrap">
                    {part.text}
                  </span>
                ) : null
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="text-left">
            <div className="inline-block bg-gray-100 px-3 py-1 rounded">
              <span>正在思考中...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleFormSubmit} className="flex gap-2">
        <input
          className="flex-1 border rounded p-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="請輸入問題..."
          disabled={isLoading}
        />
        <button
          type="submit"
          className="bg-black text-white px-4 rounded disabled:opacity-50"
          disabled={isLoading}>
          {isLoading ? "發送中..." : "發送"}
        </button>
      </form>
    </div>
  )
}
