"""文档加载器 - 支持 PDF / DOCX / TXT"""
import os
from typing import List
from langchain_core.documents import Document


def load_document(file_path: str) -> List[Document]:
    """根据文件后缀选择对应的加载器，返回 LangChain Document 列表。"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        # 给每个文档块打上来源标记
        for doc in docs:
            doc.metadata["source"] = os.path.basename(file_path)
            doc.metadata["file_type"] = "pdf"
        return docs

    elif ext in (".docx", ".doc"):
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = os.path.basename(file_path)
            doc.metadata["file_type"] = "word"
        return docs

    elif ext == ".txt":
        from langchain_community.document_loaders import TextLoader
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = os.path.basename(file_path)
            doc.metadata["file_type"] = "txt"
        return docs

    else:
        raise ValueError(f"不支持的文件类型: {ext}，仅支持 PDF / DOCX / TXT")
