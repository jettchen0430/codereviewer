import os
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from ..models.rag import Document, RetrievalResult, EmbeddingConfig, VectorStoreConfig
from ..config.settings import settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG 引擎，负责文档检索和知识增强"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.vector_store_config = VectorStoreConfig()
        self.documents: List[Document] = []
        self.index = None
        self.embedding_model = None
        self._initialize()
    
    def _initialize(self):
        """初始化RAG引擎"""
        try:
            # 加载嵌入模型
            self.embedding_model = SentenceTransformer(self.config.model_name)
            if self.config.device != "cpu":
                self.embedding_model = self.embedding_model.to(self.config.device)
            
            # 加载文档
            self._load_documents()
            
            # 构建向量索引
            self._build_index()
            
            logger.info("RAG engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            raise
    
    def _load_documents(self):
        """从文件加载文档"""
        try:
            documents_file = settings.documents_file
            if not os.path.exists(documents_file):
                logger.warning(f"Documents file {documents_file} not found, using default documents")
                self._load_default_documents()
                return
            
            with open(documents_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    doc = Document(
                        id=f"doc_{i}",
                        content=line,
                        metadata={"source": documents_file, "line": i + 1}
                    )
                    self.documents.append(doc)
            
            logger.info(f"Loaded {len(self.documents)} documents from {documents_file}")
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            self._load_default_documents()
    
    def _load_default_documents(self):
        """加载默认文档"""
        default_docs = [
            "Always use descriptive variable names that clearly indicate their purpose.",
            "Avoid magic numbers in code; use named constants instead.",
            "Ensure proper error handling in functions with try-catch blocks.",
            "Follow the project's established indentation and formatting style.",
            "Write clear and concise comments for complex logic.",
            "Use meaningful function names that describe what the function does.",
            "Implement proper input validation for all user inputs.",
            "Avoid deep nesting in control structures; prefer early returns.",
            "Use consistent naming conventions throughout the codebase.",
            "Ensure all functions have a single responsibility and clear purpose."
        ]
        
        for i, content in enumerate(default_docs):
            doc = Document(
                id=f"default_{i}",
                content=content,
                metadata={"source": "default", "category": "best_practices"}
            )
            self.documents.append(doc)
        
        logger.info(f"Loaded {len(default_docs)} default documents")
    
    def _build_index(self):
        """构建向量索引"""
        if not self.documents:
            logger.warning("No documents to index")
            return
        
        try:
            # 生成文档嵌入
            texts = [doc.content for doc in self.documents]
            embeddings = self.embedding_model.encode(texts, normalize_embeddings=self.config.normalize)
            
            # 创建FAISS索引
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # 使用内积相似度
            
            # 添加向量到索引
            self.index.add(embeddings.astype('float32'))
            
            # 存储嵌入向量到文档对象
            for i, doc in enumerate(self.documents):
                doc.embedding = embeddings[i].tolist()
            
            logger.info(f"Built FAISS index with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            raise
    
    def retrieve(self, query: str, k: Optional[int] = None) -> RetrievalResult:
        """检索相关文档"""
        if not self.index or not self.documents:
            logger.warning("Index not built or no documents available")
            return RetrievalResult(query=query, documents=[], scores=[], total_results=0)
        
        try:
            k = k or self.vector_store_config.max_results
            
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode([query], normalize_embeddings=self.config.normalize)
            
            # 搜索相似文档
            scores, indices = self.index.search(query_embedding.astype('float32'), k)
            
            # 过滤低相似度结果
            threshold = self.vector_store_config.similarity_threshold
            filtered_results = []
            filtered_scores = []
            
            for i, score in zip(indices[0], scores[0]):
                if score >= threshold and i < len(self.documents):
                    filtered_results.append(self.documents[i])
                    filtered_scores.append(float(score))
            
            return RetrievalResult(
                query=query,
                documents=filtered_results,
                scores=filtered_scores,
                total_results=len(filtered_results)
            )
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return RetrievalResult(query=query, documents=[], scores=[], total_results=0)
    
    def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """添加新文档到知识库"""
        try:
            # 创建新文档
            doc_id = f"doc_{len(self.documents)}"
            doc = Document(
                id=doc_id,
                content=content,
                metadata=metadata or {}
            )
            
            # 生成嵌入
            embedding = self.embedding_model.encode([content], normalize_embeddings=self.config.normalize)
            doc.embedding = embedding[0].tolist()
            
            # 添加到文档列表
            self.index.add(embedding.astype('float32'))
            
            # 添加到文档列表
            self.documents.append(doc)
            
            logger.info(f"Added document {doc_id} to knowledge base")
            return True
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def get_knowledge_context(self, query: str) -> str:
        """获取知识上下文"""
        result = self.retrieve(query)
        if not result.documents:
            return ""
        
        context_parts = []
        for doc in result.documents:
            context_parts.append(doc.content)
        
        return "\n".join(context_parts)
    
    def update_documents_file(self):
        """更新文档文件"""
        try:
            documents_file = settings.documents_file
            with open(documents_file, 'w', encoding='utf-8') as f:
                for doc in self.documents:
                    if doc.metadata.get('source') != 'default':
                        f.write(f"{doc.content}\n")
            
            logger.info(f"Updated documents file {documents_file}")
        except Exception as e:
            logger.error(f"Failed to update documents file: {e}")


# 全局RAG引擎实例
rag_engine = RAGEngine() 