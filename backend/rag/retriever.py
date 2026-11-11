"""RAG Retriever - uses native ChromaDB with manual embedding"""
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from .vector_store import _get_collection_for_role
from .embeddings import get_embeddings
from lc.llm import get_chat_model

PROMPT = "You are a campus AI assistant. Answer based on the following knowledge base content.\n"
PROMPT += "If the information is not available, say so honestly.\n\n"
PROMPT += "Knowledge base:\n{context}\n\nQuestion: {question}\nAnswer:"
RAG_PROMPT = PromptTemplate(template=PROMPT, input_variables=["context", "question"])

_ef = None

def _get_ef():
    global _ef
    if _ef is None:
        _ef = get_embeddings()
    return _ef

def _search(question, k, role):
    col = _get_collection_for_role(role)
    ef = _get_ef()
    emb = ef(input=[question])
    results = col.query(query_embeddings=emb, n_results=k)
    docs = []
    if results.get('documents') and results['documents'][0]:
        for i, content in enumerate(results['documents'][0]):
            meta = {}
            if results.get('metadatas') and results['metadatas'][0][i]:
                meta = results['metadatas'][0][i] or {}
            docs.append(Document(page_content=content, metadata=meta))
    return docs

def retrieve_docs(query, k=4, role="student"):
    return _search(query, k, role)

def get_qa_chain(k=None, role="student"):
    llm = get_chat_model()
    def fmt(docs): return "\n\n".join(d.page_content for d in docs)
    def run(d): return fmt(_search(d["query"], k or 4, role))
    chain = (
        {"context": RunnableLambda(run),
         "question": RunnableLambda(lambda d: d["query"])}
        | RAG_PROMPT | llm | StrOutputParser()
    )
    return chain