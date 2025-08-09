import { NextRequest, NextResponse } from 'next/server'
import { signOut } from '@/auth'

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { callbackUrl = '/' } = body
        
        // 執行登出
        await signOut({
            redirectTo: callbackUrl,
            redirect: false
        })
        
        return NextResponse.json({
            success: true,
            message: '登出成功',
            redirectUrl: callbackUrl
        })
    } catch (error) {
        console.error('Logout error:', error)
        return NextResponse.json(
            { 
                success: false, 
                error: '登出失敗',
                message: error instanceof Error ? error.message : '未知錯誤'
            },
            { status: 500 }
        )
    }
}

// GET 方法用於登出
export async function GET() {
    try {
        await signOut({ redirectTo: '/' })
        return NextResponse.redirect('/')
    } catch (error) {
        console.error('Logout error:', error)
        return NextResponse.json(
            { error: '登出失敗' },
            { status: 500 }
        )
    }
}