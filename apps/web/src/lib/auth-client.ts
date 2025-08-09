// 客戶端認證工具函數

export interface AuthResponse {
    success: boolean
    message?: string
    error?: string
    redirectUrl?: string
}

export interface SessionData {
    authenticated: boolean
    user: {
        name?: string
        email?: string
        image?: string
        lineId?: string
        role?: string
        isActive?: boolean
    } | null
}

/**
 * 執行登入
 */
export async function loginAPI(callbackUrl = '/dashboard'): Promise<AuthResponse> {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                provider: 'line',
                callbackUrl
            })
        })
        
        const data = await response.json()
        
        if (!response.ok) {
            throw new Error(data.message || '登入失敗')
        }
        
        return data
    } catch (error) {
        console.error('Login API error:', error)
        return {
            success: false,
            error: error instanceof Error ? error.message : '登入失敗'
        }
    }
}

/**
 * 執行登出
 */
export async function logoutAPI(callbackUrl = '/'): Promise<AuthResponse> {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ callbackUrl })
        })
        
        const data = await response.json()
        
        if (!response.ok) {
            throw new Error(data.message || '登出失敗')
        }
        
        return data
    } catch (error) {
        console.error('Logout API error:', error)
        return {
            success: false,
            error: error instanceof Error ? error.message : '登出失敗'
        }
    }
}

/**
 * 取得當前用戶會話資訊
 */
export async function getSessionAPI(): Promise<SessionData> {
    try {
        const response = await fetch('/api/auth/session', {
            method: 'GET',
            credentials: 'include'
        })
        
        if (!response.ok) {
            throw new Error('無法取得會話資訊')
        }
        
        return await response.json()
    } catch (error) {
        console.error('Session API error:', error)
        return {
            authenticated: false,
            user: null
        }
    }
}

/**
 * 檢查用戶權限
 */
export function hasPermission(userRole?: string, requiredRole: 'admin' | 'cs' = 'cs'): boolean {
    if (!userRole) return false
    
    if (requiredRole === 'cs') {
        return ['admin', 'cs'].includes(userRole)
    }
    
    return userRole === 'admin'
}

/**
 * React Hook 用於認證狀態
 */
import { useState, useEffect } from 'react'

export function useAuth() {
    const [session, setSession] = useState<SessionData>({ authenticated: false, user: null })
    const [loading, setLoading] = useState(true)
    
    useEffect(() => {
        getSessionAPI()
            .then(setSession)
            .finally(() => setLoading(false))
    }, [])
    
    const login = async (callbackUrl?: string) => {
        const result = await loginAPI(callbackUrl)
        if (result.success && result.redirectUrl) {
            window.location.href = result.redirectUrl
        }
        return result
    }
    
    const logout = async (callbackUrl?: string) => {
        const result = await logoutAPI(callbackUrl)
        if (result.success) {
            setSession({ authenticated: false, user: null })
            if (result.redirectUrl) {
                window.location.href = result.redirectUrl
            }
        }
        return result
    }
    
    return {
        ...session,
        loading,
        login,
        logout,
        isAdmin: session.user?.role === 'admin',
        isCS: hasPermission(session.user?.role),
        hasRole: (role: 'admin' | 'cs') => hasPermission(session.user?.role, role)
    }
}