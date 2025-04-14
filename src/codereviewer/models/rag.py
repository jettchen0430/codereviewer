from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Document:
    """文档模型"""
    content: str
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "content": self.content,
            "embedding": self.embedding
        }

@dataclass
class SearchResult:
    """检索结果模型"""
    document: Document
    score: float
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "document": self.document.to_dict(),
            "score": self.score
        } 