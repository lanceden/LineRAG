"""
知識圖譜相關的 Pydantic 模型
定義 API 請求和回應的資料結構
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class EntityModel(BaseModel):
    """實體模型"""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    distance: Optional[int] = None  # 用於相關實體的距離


class KnowledgeGraphQueryRequest(BaseModel):
    """知識圖譜查詢請求"""
    company_id: int = Field(..., description="公司 ID")
    entity_name: str = Field(..., description="要搜尋的實體名稱")
    max_depth: int = Field(default=2, description="最大搜尋深度", ge=1, le=5)


class KnowledgeGraphQueryResponse(BaseModel):
    """知識圖譜查詢回應"""
    status: str
    message: str
    entities: List[EntityModel]
    related_entities: List[EntityModel]


class GraphStatsModel(BaseModel):
    """圖譜統計模型"""
    entity_count: int = Field(default=0, description="實體數量")
    document_count: int = Field(default=0, description="文檔數量")
    relationship_count: int = Field(default=0, description="關係數量")


class KnowledgeGraphStatsResponse(BaseModel):
    """知識圖譜統計回應"""
    status: str
    company_id: int
    stats: GraphStatsModel


class CreateEntityRequest(BaseModel):
    """建立實體請求"""
    company_id: int = Field(..., description="公司 ID")
    name: str = Field(..., description="實體名稱")
    type: str = Field(..., description="實體類型")
    description: Optional[str] = Field(None, description="實體描述")
    properties: Optional[Dict[str, Any]] = Field(None, description="實體屬性")


class CreateRelationshipRequest(BaseModel):
    """建立關係請求"""
    company_id: int = Field(..., description="公司 ID")
    source_entity_id: str = Field(..., description="來源實體 ID")
    target_entity_id: str = Field(..., description="目標實體 ID")
    relationship_type: str = Field(..., description="關係類型")
    properties: Optional[Dict[str, Any]] = Field(None, description="關係屬性")


class DocumentGraphRequest(BaseModel):
    """文檔圖譜建立請求"""
    company_id: int = Field(..., description="公司 ID")
    document_id: str = Field(..., description="文檔 ID")
    filename: str = Field(..., description="檔案名稱")
    file_path: str = Field(..., description="檔案路徑")
    file_type: Optional[str] = Field(None, description="檔案類型")
    file_size: Optional[int] = Field(None, description="檔案大小")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文檔元資料")


class GraphVisualizationRequest(BaseModel):
    """圖譜視覺化請求"""
    company_id: int = Field(..., description="公司 ID")
    entity_id: Optional[str] = Field(None, description="中心實體 ID")
    max_nodes: int = Field(default=50, description="最大節點數量", ge=10, le=200)
    max_depth: int = Field(default=2, description="最大深度", ge=1, le=4)


class GraphNodeModel(BaseModel):
    """圖譜節點模型"""
    id: str
    label: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class GraphEdgeModel(BaseModel):
    """圖譜邊模型"""
    source: str
    target: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class GraphVisualizationResponse(BaseModel):
    """圖譜視覺化回應"""
    status: str
    message: str
    nodes: List[GraphNodeModel]
    edges: List[GraphEdgeModel]
    stats: GraphStatsModel
