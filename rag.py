# 文档库示例
documents = [
    "Always use descriptive variable names.",
    "Avoid magic numbers in code.",
    "Ensure proper error handling in functions.",
    "Follow the project's indentation style.",
    # 添加更多相关文档
]

from transformers import AutoTokenizer, AutoModel
import torch
import faiss
import numpy as np

# 加载嵌入模型和分词器
embed_tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
embed_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# 生成嵌入的函数
def get_embeddings(texts):
    inputs = embed_tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = embed_model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy()  # 平均池化得到句子嵌入

# 为文档生成嵌入并构建索引
doc_embeddings = get_embeddings(documents)
index = faiss.IndexFlatL2(doc_embeddings.shape[1])  # 使用 L2 距离
index.add(doc_embeddings)

# 检索函数
def retrieve(query, k=2):
    query_embedding = get_embeddings([query])
    distances, indices = index.search(query_embedding, k)  # 检索 k 个最相关文档
    return [documents[i] for i in indices[0]]