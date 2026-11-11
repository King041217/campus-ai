from langchain_core.prompts import ChatPromptTemplate
from prompts.templates import AI_BUDDY, CUSTOMER_SERVICE, ANALYSIS_REPORT

SYSTEM_TEXTS = {
    "ai_buddy": AI_BUDDY.to_system_message(),
    "customer_service": CUSTOMER_SERVICE.to_system_message(),
    "analysis_report": ANALYSIS_REPORT.to_system_message(),
}

def get_prompt_template(template_key: str = "ai_buddy") -> ChatPromptTemplate:
    system_text = SYSTEM_TEXTS.get(template_key, SYSTEM_TEXTS["ai_buddy"])

    NOISE_RULE = (
        "CRITICAL RULE - NEVER output reasoning or analysis steps. "
        "Do NOT start with phrases like '嗯，用户问了', '需要明确', '准备', '想到'. "
        "ONLY output the direct answer to the user."
    )

    return ChatPromptTemplate.from_messages([
        ("system", NOISE_RULE + "\n\n" + system_text),
        ("human", "{history_text}"),
        ("human", "{user_input}"),
    ])