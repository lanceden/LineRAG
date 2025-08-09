import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const useOCR = formData.get('use_ocr') === 'true'
    
    if (!file) {
      return NextResponse.json(
        { error: '沒有選擇檔案' },
        { status: 400 }
      )
    }

    // 檢查檔案類型
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    const allowedExtensions = ['.pdf', '.doc', '.docx']
    const fileExtension = path.extname(file.name).toLowerCase()
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      return NextResponse.json(
        { error: '不支援的檔案格式，請上傳 PDF 或 Word 檔案' },
        { status: 400 }
      )
    }

    // 檢查檔案大小 (限制 10MB)
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      return NextResponse.json(
        { error: '檔案大小超過限制 (10MB)' },
        { status: 400 }
      )
    }

    // 創建上傳目錄
    const uploadDir = path.join(process.cwd(), 'uploads')
    if (!existsSync(uploadDir)) {
      await mkdir(uploadDir, { recursive: true })
    }

    // 生成唯一檔案名
    const timestamp = Date.now()
    const originalName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_') // 清理檔案名
    const fileName = `${timestamp}_${originalName}`
    const filePath = path.join(uploadDir, fileName)

    // 儲存檔案
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filePath, buffer)

    // 呼叫 Python API 處理檔案
    try {
      const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8001'
      const processResponse = await fetch(`${pythonApiUrl}/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: filePath,
          original_name: file.name,
          use_ocr: useOCR
        })
      })

      if (!processResponse.ok) {
        const errorData = await processResponse.text()
        console.error('Python API error:', errorData)
        return NextResponse.json(
          { error: '檔案處理失敗，請稍後再試' },
          { status: 500 }
        )
      }

      const result = await processResponse.json()
      
      return NextResponse.json({
        message: `檔案上傳並處理成功 (${useOCR ? 'OCR 模式' : '傳統模式'})`,
        fileName: file.name,
        size: file.size,
        doc_id: result.doc_id,
        processed: true,
        processing_method: useOCR ? 'ocr' : 'traditional'
      })

    } catch (processError) {
      console.error('Processing error:', processError)
      
      // 即使處理失敗，檔案也已上傳成功
      return NextResponse.json({
        message: '檔案上傳成功，但處理時發生錯誤',
        fileName: file.name,
        size: file.size,
        processed: false,
        warning: '檔案已儲存，但尚未加入知識庫。請聯繫管理員。'
      })
    }

  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json(
      { error: '上傳失敗，請稍後再試' },
      { status: 500 }
    )
  }
}

// 獲取已上傳檔案列表
export async function GET() {
  try {
    const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8001'
    const response = await fetch(`${pythonApiUrl}/documents`)
    
    if (!response.ok) {
      throw new Error('無法獲取檔案列表')
    }
    
    const documents = await response.json()
    return NextResponse.json(documents)
    
  } catch (error) {
    console.error('Get documents error:', error)
    return NextResponse.json(
      { error: '獲取檔案列表失敗' },
      { status: 500 }
    )
  }
}

// 刪除文檔
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const docId = searchParams.get('docId')
    
    if (!docId) {
      return NextResponse.json(
        { error: '缺少文檔 ID' },
        { status: 400 }
      )
    }

    const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8001'
    const response = await fetch(`${pythonApiUrl}/documents/${docId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      const errorData = await response.json()
      return NextResponse.json(
        { error: errorData.detail || '刪除文檔失敗' },
        { status: response.status }
      )
    }

    const result = await response.json()
    return NextResponse.json(result)

  } catch (error) {
    console.error('Delete document error:', error)
    return NextResponse.json(
      { error: '刪除文檔時發生錯誤' },
      { status: 500 }
    )
  }
}