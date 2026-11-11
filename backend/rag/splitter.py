"""文本分割器 - 递归按字符分割，适配中英文混合文档"""
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_text_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> RecursiveCharacterTextSplitter:
    """创建针对中文优化的文本分割器。

    separators 按优先级递减：先尝试双换行，再单换行，句号/问号/感叹号，
    然后是逗号等次级分隔符，最后按字符硬切。
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            "；",
            "，",
            " ",
            "",
        ],
    )
