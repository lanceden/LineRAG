"use client"

import { useState } from "react"

interface Message {
  id: string
  role: "user" | "assistant"
  parts: { type: "text"; text: string }[]
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      parts: [{ type: "text", text }],
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

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
                  assistantText = data.text
                }
              } catch (e) {
                console.error("Failed to parse JSON:", e)
              }
            }
          }
        }
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        parts: [{ type: "text", text: assistantText || "回覆失敗" }],
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        parts: [{ type: "text", text: "發送訊息時發生錯誤，請稍後再試" }],
      }
      setMessages((prev) => [...prev, errorMessage])
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
