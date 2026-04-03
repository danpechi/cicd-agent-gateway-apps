"""
Zscaler Email Generation Agent
Runs in-process inside the Databricks App — no Model Serving endpoint needed.
Uses ChatDatabricks → databricks-claude-sonnet-4-5 via FMAPI.
"""

import mlflow
from langchain_core.messages import HumanMessage, SystemMessage
from databricks_langchain import ChatDatabricks

# Auto-captures every LLM call as an MLflow trace (no config needed).
mlflow.langchain.autolog()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior Zscaler sales representative with deep expertise in zero-trust
network security, cloud security, and digital transformation. You write
professional, concise sales emails that speak directly to each prospect's
industry and security challenges.

Your emails:
- Open with a hook tied to the prospect's specific industry pain points
- Explain clearly how Zscaler solves those problems (SASE, ZPA, ZIA, ZDX)
- Include one relevant customer success metric or case study reference
- End with a clear, low-friction call to action
- Are 200-350 words — never longer
- Sound human and confident, not generic or template-like

Do NOT include subject lines unless specifically requested.
Do NOT use placeholder brackets like [COMPANY NAME] — use the actual values provided.
"""

# ---------------------------------------------------------------------------
# Model — initialised once, reused across Streamlit reruns
# ---------------------------------------------------------------------------

_model = ChatDatabricks(
    endpoint="databricks-claude-sonnet-4-5",
    max_tokens=600,
    temperature=0.75,
)


def generate_email(user_prompt: str) -> str:
    """Generate a Zscaler sales email for the given prospect prompt."""
    response = _model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    return response.content
