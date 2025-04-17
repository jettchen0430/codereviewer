import numpy as np
import faiss
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from ..models.rag import Document, SearchResult
from ..config.settings import settings
from ..utils.logger import logger

class RAGUtils:
    """RAG工具类"""
    
    def __init__(self):
        self.index = None
        self.documents = []
        self.model = None
        self._load_model()
        self._load_documents()
    
    def _load_model(self) -> None:
        """加载embedding模型"""
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
    
    def _load_documents(self) -> None:
        """加载文档库"""
        try:
            with open(settings.DOCUMENTS_FILE, 'r', encoding='utf-8') as f:
                self.documents = [Document(line.strip()) for line in f.readlines()]
            
            if self.documents and self.model:
                # 获取文档的embeddings
                embeddings = self._get_embeddings([doc.content for doc in self.documents])
                for doc, emb in zip(self.documents, embeddings):
                    doc.embedding = emb
                
                # 构建FAISS索引
                dimension = len(embeddings[0])
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(embeddings).astype('float32'))
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本的embeddings"""
        if not self.model:
            return [[0.1] * settings.EMBEDDING_DIMENSION for _ in texts]
        
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.1] * settings.EMBEDDING_DIMENSION for _ in texts]
    
    def search(self, query: str, k: int = 2) -> List[SearchResult]:
        """检索相关文档"""
        if not self.index or not self.documents:
            return []
        
        try:
            # 获取查询的embedding
            query_embedding = self._get_embeddings([query])[0]
            
            # 搜索最相似的文档
            distances, indices = self.index.search(
                np.array([query_embedding]).astype('float32'),
                k
            )
            
            # 构建搜索结果
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.documents):
                    results.append(SearchResult(
                        document=self.documents[idx],
                        score=float(1 / (1 + distance))  # 将距离转换为相似度分数
                    ))
            
            return results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

# 创建全局RAG工具实例
rag_utils = RAGUtils() 