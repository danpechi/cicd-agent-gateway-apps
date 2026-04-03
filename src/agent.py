"""
Zscaler Email Generation Agent
MLflow ChatModel — calls FMAPI (databricks-meta-llama-3-3-70b-instruct)
to generate personalised sales outreach emails.
"""

import mlflow
from mlflow.deployments import get_deploy_client
from mlflow.pyfunc import ChatModel
from mlflow.types.llm import (
    ChatCompletionResponse,
    ChatMessage,
    ChatChoice,
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
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
# Email type prompts
# ---------------------------------------------------------------------------

_EMAIL_TEMPLATES = {
    "Cold Outreach": (
        "Write a cold outreach email introducing Zscaler to this prospect. "
        "Emphasise the risks of their current legacy network architecture and "
        "how Zscaler's zero-trust platform eliminates those risks."
    ),
    "Post-Demo Follow-Up": (
        "Write a follow-up email after a product demo. Recap the key value "
        "points shown, address any likely objections, and propose clear next steps."
    ),
    "Security Incident Response": (
        "Write an email responding to a recent publicised security incident "
        "at this company or in their industry. Position Zscaler as the solution "
        "that would have prevented or contained the breach."
    ),
    "Executive Business Review": (
        "Write an email requesting an executive business review (EBR) meeting. "
        "Frame it around Zscaler's strategic roadmap and how it aligns with "
        "the prospect's digital transformation priorities."
    ),
    "Renewal / Upsell": (
        "Write a renewal or upsell email targeting an existing customer. "
        "Highlight adoption metrics, new capabilities (e.g. ZDX, DSPM, AI-powered "
        "threat detection), and the risk of not expanding coverage."
    ),
}

# ---------------------------------------------------------------------------
# ChatModel
# ---------------------------------------------------------------------------

class ZscalerEmailAgent(ChatModel):
    """
    Accepts standard chat messages. The last user message should describe
    the target customer and email type. Returns a generated sales email.
    """

    def predict(
        self,
        context,
        messages: list[ChatMessage],
        params=None,
    ) -> ChatCompletionResponse:
        user_msg = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )

        # mlflow.deployments handles auth automatically in Model Serving runtime —
        # no explicit host/token needed.
        client = get_deploy_client("databricks")

        response = client.predict(
            endpoint="databricks-meta-llama-3-3-70b-instruct",
            inputs={
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                "max_tokens": 600,
                "temperature": 0.75,
            },
        )

        response_text = response["choices"][0]["message"]["content"]

        return ChatCompletionResponse(
            choices=[
                ChatChoice(
                    message=ChatMessage(role="assistant", content=response_text)
                )
            ]
        )


mlflow.models.set_model(ZscalerEmailAgent())
