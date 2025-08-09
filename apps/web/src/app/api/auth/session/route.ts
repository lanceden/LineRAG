import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/auth'

export async function GET(request: NextRequest) {
    try {
        const session = await auth()
        
        if (!session) {
            return NextResponse.json({
                authenticated: false,
                user: null
            })
        }
        
        return NextResponse.json({
            authenticated: true,
            user: {
                name: session.user?.name,
                email: session.user?.email,
                image: session.user?.image,
                lineId: session.user?.lineId,
                role: session.user?.role || 'cs',
                isActive: session.user?.isActive ?? true
            }
        })
    } catch (error) {
        console.error('Session check error:', error)
        return NextResponse.json(
            { 
                authenticated: false,
                error: '無法取得用戶資訊'
            },
            { status: 500 }
        )
    }
}