// app/api/ask/route.ts
import { NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
    const { messages } = await req.json()

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 60000)

    try {
        // 構建符合後端期望的請求格式
        const requestBody = {
            messages: messages,
            trigger: "user"
        }

        const res = await fetch('http://localhost:8000/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
            signal: controller.signal,
        })
        clearTimeout(timeout)

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`)
        }

        const data = await res.json()
        const answer = data.answer || '回覆失敗'

        // 回傳流式文字回應
        const encoder = new TextEncoder()

        const stream = new ReadableStream({
            start(controller) {
                // 發送回應文字
                controller.enqueue(encoder.encode(`data: ${JSON.stringify({
                    type: 'text',
                    text: answer
                })}\n\n`))

                // 結束流
                controller.enqueue(encoder.encode('data: [DONE]\n\n'))
                controller.close()
            }
        })

        return new Response(stream, {
            headers: {
                'Content-Type': 'text/plain; charset=utf-8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        })

    } catch (err) {
        clearTimeout(timeout)
        console.error('API Error:', err)

        const encoder = new TextEncoder()
        const stream = new ReadableStream({
            start(controller) {
                controller.enqueue(encoder.encode(`data: ${JSON.stringify({
                    type: 'text',
                    text: '伺服器逾時或發生錯誤，請稍後再試'
                })}\n\n`))
                controller.enqueue(encoder.encode('data: [DONE]\n\n'))
                controller.close()
            }
        })

        return new Response(stream, {
            headers: {
                'Content-Type': 'text/plain; charset=utf-8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        })
    }
}
