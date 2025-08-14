'use client'

import React, { useState, useCallback } from 'react'
import { 
  Building2, 
  Upload, 
  X, 
  Globe, 
  Mail, 
  Phone, 
  MapPin,
  Save,
  Loader2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Company, CreateCompanyRequest, UpdateCompanyRequest } from '@/types/company'

interface CompanyFormProps {
  company?: Company | null
  onSubmit: (data: CreateCompanyRequest | UpdateCompanyRequest) => Promise<void>
  onCancel: () => void
  loading?: boolean
  className?: string
}

export function CompanyForm({
  company,
  onSubmit,
  onCancel,
  loading = false,
  className,
}: CompanyFormProps) {
  const [formData, setFormData] = useState({
    name: company?.name || '',
    description: company?.description || '',
    website: company?.website || '',
    phone: company?.phone || '',
    email: company?.email || '',
    address: company?.address || '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string | null>(company?.logo_url || null)

  // 處理輸入變更
  const handleInputChange = useCallback((field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // 清除該欄位的錯誤
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }, [errors])

  // 處理 Logo 上傳
  const handleLogoChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // 檢查檔案類型
      if (!file.type.startsWith('image/')) {
        setErrors(prev => ({ ...prev, logo: '請選擇圖片檔案' }))
        return
      }

      // 檢查檔案大小 (2MB)
      if (file.size > 2 * 1024 * 1024) {
        setErrors(prev => ({ ...prev, logo: '圖片大小不能超過 2MB' }))
        return
      }

      setLogoFile(file)
      setErrors(prev => ({ ...prev, logo: '' }))

      // 產生預覽
      const reader = new FileReader()
      reader.onload = (e) => {
        setLogoPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }, [])

  // 移除 Logo
  const handleRemoveLogo = useCallback(() => {
    setLogoFile(null)
    setLogoPreview(null)
  }, [])

  // 表單驗證
  const validateForm = useCallback(() => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = '公司名稱為必填項目'
    } else if (formData.name.length < 2) {
      newErrors.name = '公司名稱至少需要 2 個字元'
    } else if (formData.name.length > 100) {
      newErrors.name = '公司名稱不能超過 100 個字元'
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '請輸入有效的電子郵件地址'
    }

    if (formData.website && !/^https?:\/\/.+/.test(formData.website)) {
      newErrors.website = '請輸入有效的網站 URL (包含 http:// 或 https://)'
    }

    if (formData.phone && !/^[\d\s\-\+\(\)]+$/.test(formData.phone)) {
      newErrors.phone = '請輸入有效的電話號碼'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [formData])

  // 處理表單提交
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      await onSubmit(formData)
    } catch (error) {
      // 錯誤處理由父組件負責
    }
  }, [formData, validateForm, onSubmit])

  return (
    <form onSubmit={handleSubmit} className={cn('space-y-6', className)}>
      {/* Logo 上傳 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          公司 Logo
        </label>
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
            {logoPreview ? (
              <img src={logoPreview} alt="Logo 預覽" className="w-full h-full object-cover" />
            ) : (
              <Building2 className="h-8 w-8 text-gray-400" />
            )}
          </div>
          <div className="flex-1">
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoChange}
              className="hidden"
              id="logo-upload"
            />
            <label
              htmlFor="logo-upload"
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
            >
              <Upload className="h-4 w-4 mr-2" />
              選擇圖片
            </label>
            {logoPreview && (
              <button
                type="button"
                onClick={handleRemoveLogo}
                className="ml-2 inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50"
              >
                <X className="h-4 w-4 mr-2" />
                移除
              </button>
            )}
            <p className="mt-1 text-xs text-gray-500">
              支援 JPG、PNG 格式，檔案大小不超過 2MB
            </p>
          </div>
        </div>
        {errors.logo && (
          <p className="mt-1 text-sm text-red-600">{errors.logo}</p>
        )}
      </div>

      {/* 基本資訊 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 公司名稱 */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            公司名稱 <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={cn(
                'pl-10 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                errors.name ? 'border-red-300' : 'border-gray-300'
              )}
              placeholder="請輸入公司名稱"
            />
          </div>
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name}</p>
          )}
        </div>

        {/* 電子郵件 */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            電子郵件
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              className={cn(
                'pl-10 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                errors.email ? 'border-red-300' : 'border-gray-300'
              )}
              placeholder="company@example.com"
            />
          </div>
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email}</p>
          )}
        </div>

        {/* 電話號碼 */}
        <div>
          <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
            電話號碼
          </label>
          <div className="relative">
            <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="tel"
              id="phone"
              value={formData.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              className={cn(
                'pl-10 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                errors.phone ? 'border-red-300' : 'border-gray-300'
              )}
              placeholder="02-1234-5678"
            />
          </div>
          {errors.phone && (
            <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
          )}
        </div>

        {/* 網站 */}
        <div>
          <label htmlFor="website" className="block text-sm font-medium text-gray-700 mb-1">
            公司網站
          </label>
          <div className="relative">
            <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="url"
              id="website"
              value={formData.website}
              onChange={(e) => handleInputChange('website', e.target.value)}
              className={cn(
                'pl-10 w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                errors.website ? 'border-red-300' : 'border-gray-300'
              )}
              placeholder="https://www.example.com"
            />
          </div>
          {errors.website && (
            <p className="mt-1 text-sm text-red-600">{errors.website}</p>
          )}
        </div>
      </div>

      {/* 公司描述 */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          公司描述
        </label>
        <textarea
          id="description"
          rows={3}
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="簡單描述您的公司業務..."
        />
      </div>

      {/* 地址 */}
      <div>
        <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
          公司地址
        </label>
        <div className="relative">
          <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <textarea
            id="address"
            rows={2}
            value={formData.address}
            onChange={(e) => handleInputChange('address', e.target.value)}
            className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="請輸入完整地址..."
          />
        </div>
      </div>

      {/* 操作按鈕 */}
      <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              {company ? '更新中...' : '建立中...'}
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              {company ? '更新公司' : '建立公司'}
            </>
          )}
        </button>
      </div>
    </form>
  )
}
