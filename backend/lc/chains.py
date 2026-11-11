'''LCEL Chains - pipe-based campus Q&A pipelines'''
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough, RunnableParallel

from .llm import get_chat_model
from .prompts import get_prompt_template

import re

def _strip_thinking(text: str) -> str:
    if not text or len(text) < 10:
        return text
    # Remove <think>...</think> tags (DeepSeek reasoning)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    if not text:
        return ''
    # Remove plain text thinking preamble
    text = text.replace('\r\n', '\n')
    parts = text.split(chr(10), 1)
    if len(parts) == 2:
        first, rest = parts
        if (re.match(r'^(嗯|好的|哦)[，,]', first.strip()) or chr(29992)+chr(25143) in first) and len(first) > 10:
            return rest.strip()
    return text.strip()

def get_simple_chain(model=None, template_key: str = "ai_buddy"):
    '''Basic LCEL chain: prompt | model | StrOutputParser

    Input: {"history_text": "...", "user_input": "hello"}
    Output: plain text reply string
    '''
    _model = model or get_chat_model(streaming=False)
    prompt = get_prompt_template(template_key)
    return prompt | _model | StrOutputParser() | RunnableLambda(lambda x: _strip_thinking(x))


def get_branch_chain(model=None):
    '''RunnableBranch chain - routes questions by type.

    Demonstrates LCEL conditional routing:
      - course-related -> course expert prompt
      - grade/exam       -> concise professional prompt
      - everything else  -> general AI buddy
    '''
    _model = model or get_chat_model(streaming=False)

    course_prompt = get_prompt_template("ai_buddy")
    exam_prompt = get_prompt_template("customer_service")
    default_prompt = get_prompt_template("ai_buddy")

    def classify(inputs: dict) -> str:
        text = inputs.get("user_input", "")
        if any(kw in text for kw in ["??", "??", "??", "??", "??"]):
            return "course"
        if any(kw in text for kw in ["??", "??", "??", "??", "??"]):
            return "exam"
        return "default"

    branch = RunnableBranch(
        (
            RunnableLambda(lambda x: classify(x) == "course"),
            course_prompt | _model | StrOutputParser(),
        ),
        (
            RunnableLambda(lambda x: classify(x) == "exam"),
            exam_prompt | _model | StrOutputParser(),
        ),
        default_prompt | _model | StrOutputParser(),
    )

    return branch


def get_demo_parallel_chain(model=None):
    '''RunnableParallel chain - generates AI buddy + analysis report simultaneously.

    Input: {"history_text": "", "user_input": "..."}
    Output: {"ai_buddy_response": "...", "analysis_response": "..."}
    '''
    _model = model or get_chat_model(streaming=False)
    buddy_chain = get_simple_chain(_model, "ai_buddy")
    analysis_chain = get_simple_chain(_model, "analysis_report")

    return RunnableParallel(
        ai_buddy_response=buddy_chain,
        analysis_response=analysis_chain,
    )
