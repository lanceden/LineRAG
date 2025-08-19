# LineRAG 權限矩陣管理系統

## 🎯 設計目標

基於健身俱樂部管理系統的矩陣式權限設計，實現簡單直觀的權限管理界面。

## 📋 權限矩陣界面設計

### 矩陣式權限管理

```bash
LineRAG 權限管理
┌─────────────────────────────────────────────────────────────────┐
│                    │ admin  │ 張小明 │ 李小華 │ 王大明 │ 陳小美 │
├─────────────────────────────────────────────────────────────────┤
│ 🏢 公司管理                                                      │
│   ├ 查看公司       │   ✓    │   ✓    │   ✓    │   ✓    │        │
│   ├ 建立公司       │   ✓    │        │        │        │        │
│   ├ 編輯公司       │   ✓    │   ✓    │        │        │        │
│   ├ 刪除公司       │   ✓    │        │        │        │        │
│   └ 公司統計       │   ✓    │   ✓    │   ✓    │        │        │
├─────────────────────────────────────────────────────────────────┤
│ 👥 用戶管理                                                      │
│   ├ 查看用戶       │   ✓    │   ✓    │        │        │        │
│   ├ 建立用戶       │   ✓    │        │        │        │        │
│   ├ 編輯用戶       │   ✓    │   ✓    │        │        │        │
│   ├ 刪除用戶       │   ✓    │        │        │        │        │
│   └ 權限管理       │   ✓    │        │        │        │        │
├─────────────────────────────────────────────────────────────────┤
│ 📄 文檔管理                                                      │
│   ├ 查看文檔       │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │
│   ├ 上傳文檔       │   ✓    │   ✓    │   ✓    │        │        │
│   ├ 編輯文檔       │   ✓    │   ✓    │        │        │        │
│   ├ 刪除文檔       │   ✓    │   ✓    │        │        │        │
│   └ 文檔統計       │   ✓    │   ✓    │   ✓    │        │        │
├─────────────────────────────────────────────────────────────────┤
│ 💬 對話管理                                                      │
│   ├ 查看對話       │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │
│   ├ 回覆對話       │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │
│   ├ 刪除對話       │   ✓    │   ✓    │        │        │        │
│   └ 對話統計       │   ✓    │   ✓    │   ✓    │        │        │
├─────────────────────────────────────────────────────────────────┤
│ 📊 報表分析                                                      │
│   ├ 查看報表       │   ✓    │   ✓    │   ✓    │        │        │
│   ├ 匯出報表       │   ✓    │   ✓    │        │        │        │
│   └ 自訂報表       │   ✓    │        │        │        │        │
├─────────────────────────────────────────────────────────────────┤
│ ⚙️ 系統設定                                                      │
│   ├ 基本設定       │   ✓    │        │        │        │        │
│   ├ AI 設定        │   ✓    │        │        │        │        │
│   └ 系統監控       │   ✓    │        │        │        │        │
└─────────────────────────────────────────────────────────────────┘

公司存取權限
┌─────────────────────────────────────────────────────────────────┐
│                    │ admin  │ 張小明 │ 李小華 │ 王大明 │ 陳小美 │
├─────────────────────────────────────────────────────────────────┤
│ 🌍 所有公司        │   ✓    │        │        │        │        │
│ 🏢 A公司           │   ✓    │   ✓    │   ✓    │   ✓    │        │
│ 🏢 B公司           │   ✓    │   ✓    │        │        │   ✓    │
│ 🏢 C公司           │   ✓    │        │   ✓    │        │        │
└─────────────────────────────────────────────────────────────────┘
```

## 🗂️ 權限功能列表

### 功能權限代碼

```javascript
const PERMISSIONS = {
  // 公司管理
  'company.view': '查看公司',
  'company.create': '建立公司', 
  'company.edit': '編輯公司',
  'company.delete': '刪除公司',
  'company.stats': '公司統計',
  
  // 用戶管理
  'user.view': '查看用戶',
  'user.create': '建立用戶',
  'user.edit': '編輯用戶', 
  'user.delete': '刪除用戶',
  'user.permission': '權限管理',
  
  // 文檔管理
  'document.view': '查看文檔',
  'document.upload': '上傳文檔',
  'document.edit': '編輯文檔',
  'document.delete': '刪除文檔',
  'document.stats': '文檔統計',
  
  // 對話管理
  'chat.view': '查看對話',
  'chat.reply': '回覆對話',
  'chat.delete': '刪除對話',
  'chat.stats': '對話統計',
  
  // 報表分析
  'report.view': '查看報表',
  'report.export': '匯出報表',
  'report.custom': '自訂報表',
  
  // 系統設定
  'system.setting': '基本設定',
  'system.ai': 'AI 設定',
  'system.monitor': '系統監控'
}
```

## 💾 資料表結構

### 用戶權限表 (user_permissions)

```sql
CREATE TABLE user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES system_users(id) ON DELETE CASCADE,
    granted_permissions TEXT[] DEFAULT '{}',    -- 功能權限代碼陣列
    accessible_companies TEXT[] DEFAULT '{}',   -- 可存取公司ID陣列 ('*'表示全部)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 權限定義表 (permissions)

```sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,        -- 權限代碼
    name VARCHAR(100) NOT NULL,               -- 權限名稱  
    category VARCHAR(50) NOT NULL,            -- 功能分類
    description TEXT,                         -- 權限描述
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎨 前端實現

### 權限矩陣組件

```tsx
function PermissionMatrix() {
  const [users, setUsers] = useState([])
  const [permissions, setPermissions] = useState({})
  const [companies, setCompanies] = useState([])

  return (
    <div className="permission-matrix">
      <h2>權限管理矩陣</h2>
      
      {/* 功能權限矩陣 */}
      <div className="matrix-section">
        <h3>功能權限</h3>
        <table className="matrix-table">
          <thead>
            <tr>
              <th>功能</th>
              {users.map(user => (
                <th key={user.id}>{user.username}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(PERMISSION_CATEGORIES).map(([category, perms]) => (
              <React.Fragment key={category}>
                <tr className="category-row">
                  <td colSpan={users.length + 1}>{category}</td>
                </tr>
                {perms.map(perm => (
                  <tr key={perm.code}>
                    <td className="permission-name">├ {perm.name}</td>
                    {users.map(user => (
                      <td key={user.id} className="checkbox-cell">
                        <input
                          type="checkbox"
                          checked={hasPermission(user.id, perm.code)}
                          onChange={(e) => togglePermission(user.id, perm.code, e.target.checked)}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* 公司存取權限矩陣 */}
      <div className="matrix-section">
        <h3>公司存取權限</h3>
        <table className="matrix-table">
          <thead>
            <tr>
              <th>公司</th>
              {users.map(user => (
                <th key={user.id}>{user.username}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>🌍 所有公司</td>
              {users.map(user => (
                <td key={user.id} className="checkbox-cell">
                  <input
                    type="checkbox"
                    checked={hasCompanyAccess(user.id, '*')}
                    onChange={(e) => toggleCompanyAccess(user.id, '*', e.target.checked)}
                  />
                </td>
              ))}
            </tr>
            {companies.map(company => (
              <tr key={company.id}>
                <td>🏢 {company.name}</td>
                {users.map(user => (
                  <td key={user.id} className="checkbox-cell">
                    <input
                      type="checkbox"
                      checked={hasCompanyAccess(user.id, company.id)}
                      onChange={(e) => toggleCompanyAccess(user.id, company.id, e.target.checked)}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

## 🔧 後端 API

### 權限管理 API

```python
@router.get("/permissions/matrix")
async def get_permission_matrix():
    """獲取權限矩陣資料"""
    users = get_all_users()
    permissions = get_all_permissions()
    companies = get_all_companies()
    user_permissions = get_all_user_permissions()
    
    return {
        "users": users,
        "permissions": permissions,
        "companies": companies,
        "matrix": user_permissions
    }

@router.post("/permissions/toggle")
async def toggle_permission(
    user_id: int,
    permission_code: str,
    granted: bool
):
    """切換用戶權限"""
    toggle_user_permission(user_id, permission_code, granted)
    return {"success": True}

@router.post("/permissions/company-access")
async def toggle_company_access(
    user_id: int, 
    company_id: str,
    granted: bool
):
    """切換公司存取權限"""
    toggle_user_company_access(user_id, company_id, granted)
    return {"success": True}
```

## 🎯 權限分配說明

### 完全彈性化權限分配

- 每個用戶的權限完全由管理員在矩陣中勾選決定
- 沒有預設角色，沒有固定權限組合
- 可以針對每個用戶的實際需求個別設定
- 支援任意權限組合，完全客製化

## ✅ 實現特色

1. **直觀視覺化**：矩陣式界面一目了然
2. **簡單操作**：直接勾選即可分配權限
3. **雙重控制**：功能權限 + 公司存取權限
4. **彈性管理**：支援個別調整和批次設定
5. **即時更新**：權限變更立即生效

完全按照健身俱樂部管理系統的設計理念，實現簡單易用的權限管理。
