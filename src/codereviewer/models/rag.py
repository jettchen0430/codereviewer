from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Document(BaseModel):
    """文档模型"""
    id: str = Field(..., description="文档唯一标识")
    content: str = Field(..., description="文档内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    embedding: Optional[List[float]] = Field(None, description="文档嵌入向量")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")


class RetrievalResult(BaseModel):
    """检索结果模型"""
    query: str = Field(..., description="检索查询")
    documents: List[Document] = Field(default_factory=list, description="检索到的文档")
    scores: List[float] = Field(default_factory=list, description="相关性分数")
    total_results: int = Field(default=0, description="总结果数")
    retrieval_time: Optional[float] = Field(None, description="检索耗时")


class KnowledgeBase(BaseModel):
    """知识库模型"""
    id: str = Field(..., description="知识库唯一标识")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    documents: List[Document] = Field(default_factory=list, description="知识库文档")
    embedding_model: str = Field(..., description="使用的嵌入模型")
    vector_store_type: str = Field(..., description="向量存储类型")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")


class EmbeddingConfig(BaseModel):
    """嵌入配置模型"""
    model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="嵌入模型名称")
    dimension: int = Field(default=384, description="嵌入维度")
    max_length: int = Field(default=512, description="最大序列长度")
    normalize: bool = Field(default=True, description="是否归一化")
    device: str = Field(default="cpu", description="计算设备")


class VectorStoreConfig(BaseModel):
    """向量存储配置模型"""
    type: str = Field(default="faiss", description="向量存储类型")
    index_path: Optional[str] = Field(None, description="索引文件路径")
    similarity_metric: str = Field(default="cosine", description="相似度度量方法")
    max_results: int = Field(default=5, description="最大返回结果数")
    similarity_threshold: float = Field(default=0, description="相似度阈值") 