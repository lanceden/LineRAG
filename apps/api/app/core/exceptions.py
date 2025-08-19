"""
自定義異常類別
"""


class BaseAPIException(Exception):
    """API 基礎異常"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundError(BaseAPIException):
    """資源不存在異常"""
    def __init__(self, message: str = "資源不存在"):
        super().__init__(message, "NOT_FOUND")


class ValidationError(BaseAPIException):
    """驗證錯誤異常"""
    def __init__(self, message: str = "驗證失敗"):
        super().__init__(message, "VALIDATION_ERROR")


class PermissionError(BaseAPIException):
    """權限不足異常"""
    def __init__(self, message: str = "權限不足"):
        super().__init__(message, "PERMISSION_DENIED")


class DuplicateError(BaseAPIException):
    """重複資源異常"""
    def __init__(self, message: str = "資源已存在"):
        super().__init__(message, "DUPLICATE_RESOURCE")


class BusinessLogicError(BaseAPIException):
    """業務邏輯錯誤異常"""
    def __init__(self, message: str = "業務邏輯錯誤"):
        super().__init__(message, "BUSINESS_LOGIC_ERROR")


class ExternalServiceError(BaseAPIException):
    """外部服務錯誤異常"""
    def __init__(self, message: str = "外部服務錯誤"):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")


class DatabaseError(BaseAPIException):
    """資料庫錯誤異常"""
    def __init__(self, message: str = "資料庫錯誤"):
        super().__init__(message, "DATABASE_ERROR")


class ConfigurationError(BaseAPIException):
    """配置錯誤異常"""
    def __init__(self, message: str = "配置錯誤"):
        super().__init__(message, "CONFIGURATION_ERROR")
