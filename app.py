"""
Zscaler Email Generator
Databricks Streamlit App — AI-powered sales outreach with AI Gateway

Tabs:
  1. ✉️  Email Generator — pick a prospect, pick a type, generate the email
  2. 📊  AI Gateway — inference table viewer, rate-limit status, usage stats
"""

import configparser
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be FIRST Streamlit command
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Zscaler Email Generator",
    page_icon="🔐",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Databricks credentials
# ---------------------------------------------------------------------------

def _db_credentials() -> tuple[str, str]:
    cfg = configparser.ConfigParser()
    cfg.read(Path.home() / ".databrickscfg")
    host  = cfg.get("DEFAULT", "host",  fallback="") or os.environ.get("DATABRICKS_HOST",  "")
    token = cfg.get("DEFAULT", "token", fallback="") or os.environ.get("DATABRICKS_TOKEN", "")
    if host and not host.startswith("http"):
        host = "https://" + host
    return host.rstrip("/"), token


HOST, TOKEN = _db_credentials()
_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type":  "application/json",
}

# ---------------------------------------------------------------------------
# SQL helper
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_warehouse_id() -> str:
    r = requests.get(f"{HOST}/api/2.0/sql/warehouses", headers=_HEADERS, timeout=15)
    r.raise_for_status()
    whs     = r.json().get("warehouses", [])
    running = [w for w in whs if w.get("state") == "RUNNING"]
    return (running or whs)[0]["id"]


def _query(sql: str) -> pd.DataFrame:
    wh_id = _get_warehouse_id()
    r = requests.post(
        f"{HOST}/api/2.0/sql/statements",
        json={
            "statement":       sql,
            "warehouse_id":    wh_id,
            "wait_timeout":    "30s",
            "on_wait_timeout": "CANCEL",
            "disposition":     "INLINE",
            "format":          "JSON_ARRAY",
        },
        headers=_HEADERS,
        timeout=45,
    )
    r.raise_for_status()
    body   = r.json()
    status = body.get("status", {}).get("state", "")
    if status != "SUCCEEDED":
        raise RuntimeError(body.get("status", {}).get("error", {}).get("message", body))
    cols = [c["name"] for c in body.get("manifest", {}).get("schema", {}).get("columns", [])]
    rows = body.get("result", {}).get("data_array", []) or []
    return pd.DataFrame(rows, columns=cols)

# ---------------------------------------------------------------------------
# Prospect catalogue — 10 realistic Zscaler target accounts
# ---------------------------------------------------------------------------

PROSPECTS = {
    "JPMorgan Chase": {
        "industry":    "Financial Services",
        "size":        "~300,000 employees",
        "hq":          "New York, NY",
        "pain_points": "Legacy VPN infrastructure across 60+ countries, high-profile breach risk, PCI-DSS / SOX compliance, insider threat detection.",
        "use_cases":   "Zero Trust Network Access (ZTPA), branch office transformation, secure cloud access (AWS, Azure, GCP).",
    },
    "Accenture": {
        "industry":    "Professional Services / Consulting",
        "size":        "~740,000 employees",
        "hq":          "Dublin, Ireland",
        "pain_points": "Massive remote workforce, thousands of client-site deployments, contractor access management, data exfiltration risk.",
        "use_cases":   "ZPA for contractor access, ZIA for internet security at scale, DSPM for client data protection.",
    },
    "Boeing": {
        "industry":    "Aerospace & Defense",
        "size":        "~170,000 employees",
        "hq":          "Arlington, VA",
        "pain_points": "Nation-state threat actors, OT/IT convergence, ITAR compliance, supply chain security.",
        "use_cases":   "Zero Trust for manufacturing floors, secure supplier portals, ZDX for application performance visibility.",
    },
    "Pfizer": {
        "industry":    "Pharmaceuticals",
        "size":        "~83,000 employees",
        "hq":          "New York, NY",
        "pain_points": "IP theft of drug research, hybrid cloud sprawl post-COVID, FDA 21 CFR Part 11 compliance.",
        "use_cases":   "ZIA Advanced Threat Protection, ZPA for lab-to-cloud access, inline CASB for SaaS.",
    },
    "Walmart": {
        "industry":    "Retail",
        "size":        "~2,100,000 employees",
        "hq":          "Bentonville, AR",
        "pain_points": "Massive POS network attack surface, PCI-DSS scope reduction, securing 10,000+ store locations.",
        "use_cases":   "Branch transformation (SD-WAN + ZIA), ZTNA for vendor access, Zero Trust segmentation.",
    },
    "General Motors": {
        "industry":    "Automotive",
        "size":        "~163,000 employees",
        "hq":          "Detroit, MI",
        "pain_points": "Connected vehicle data pipelines, ransomware exposure in plants, M&A integration security.",
        "use_cases":   "OT security posture, secure DevOps for connected car platform, ZPA for M&A network integration.",
    },
    "ExxonMobil": {
        "industry":    "Energy / Oil & Gas",
        "size":        "~62,000 employees",
        "hq":          "Spring, TX",
        "pain_points": "Critical infrastructure targeting, SCADA / OT exposure, remote rig access security.",
        "use_cases":   "Zero Trust for remote operations, ZIA for offshore connectivity, OT visibility and segmentation.",
    },
    "Lockheed Martin": {
        "industry":    "Defense & Aerospace",
        "size":        "~114,000 employees",
        "hq":          "Bethesda, MD",
        "pain_points": "Classified data access controls, CMMC 2.0 compliance, nation-state persistent threats.",
        "use_cases":   "ZPA for classified environments, FIPS-140 validated controls, microsegmentation.",
    },
    "Johnson & Johnson": {
        "industry":    "Healthcare",
        "size":        "~135,000 employees",
        "hq":          "New Brunswick, NJ",
        "pain_points": "Medical device security, HIPAA and GDPR across 60 countries, post-divestiture network separation.",
        "use_cases":   "ZIA for hospital network traffic, ZPA for clinical app access, DSPM for patient data.",
    },
    "Microsoft": {
        "industry":    "Technology",
        "size":        "~220,000 employees",
        "hq":          "Redmond, WA",
        "pain_points": "Securing hybrid workforce, third-party developer access, supply chain integrity post-SolarWinds.",
        "use_cases":   "ZPA for dev environment access, ZDX for global workforce experience, AI-powered threat detection.",
    },
}

EMAIL_TYPES = [
    "Cold Outreach",
    "Post-Demo Follow-Up",
    "Security Incident Response",
    "Executive Business Review",
    "Renewal / Upsell",
]

# ---------------------------------------------------------------------------
# Agent call helper
# ---------------------------------------------------------------------------

def call_agent(endpoint_name: str, prompt: str) -> str:
    r = requests.post(
        f"{HOST}/serving-endpoints/{endpoint_name}/invocations",
        json={"messages": [{"role": "user", "content": prompt}]},
        headers=_HEADERS,
        timeout=90,
    )
    r.raise_for_status()
    body = r.json()
    # Support both chat completion and direct output formats
    if "choices" in body:
        return body["choices"][0]["message"]["content"]
    output = body.get("output", [])
    if output and isinstance(output, list):
        last = output[-1]
        if isinstance(last, dict):
            content = last.get("content", "")
            if isinstance(content, list):
                return "".join(c.get("text", "") for c in content if isinstance(c, dict))
            return str(content)
    return str(body)

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image(
        "https://www.zscaler.com/themes/custom/zscaler/logo.svg",
        width=160,
    ) if False else st.markdown("## 🔐 Zscaler Email Generator")

    st.markdown("---")
    st.subheader("Configuration")
    agent_endpoint = st.text_input(
        "Agent Endpoint Name",
        value=os.environ.get("AGENT_ENDPOINT", ""),
        placeholder="zscaler-email-yourname",
        help="Copy the endpoint name printed in the setup job logs.",
    )

    catalog = st.text_input("UC Catalog", value=os.environ.get("UC_CATALOG", "main"))
    schema  = st.text_input("UC Schema",  value=os.environ.get("UC_SCHEMA",  "zscaler"))

    st.markdown("---")
    st.caption("AI Gateway enabled on this endpoint provides inference tables, rate limiting, and usage tracking.")

# ---------------------------------------------------------------------------
# App header
# ---------------------------------------------------------------------------

st.title("🔐 Zscaler Email Generator")
st.caption(
    "AI-powered sales outreach — select a prospect, choose an email type, "
    "and let the agent draft a personalised email. "
    "Every request is logged via AI Gateway inference tables."
)

tab_generate, tab_gateway = st.tabs(["✉️ Email Generator", "📊 AI Gateway"])

# ===========================================================================
# TAB 1 — EMAIL GENERATOR
# ===========================================================================

with tab_generate:

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Prospect & Email Settings")

        prospect_name = st.selectbox(
            "Target Account",
            options=list(PROSPECTS.keys()),
        )
        prospect = PROSPECTS[prospect_name]

        email_type = st.selectbox("Email Type", options=EMAIL_TYPES)

        with st.expander("Account Brief", expanded=True):
            st.markdown(f"**Industry:** {prospect['industry']}")
            st.markdown(f"**Size:** {prospect['size']}")
            st.markdown(f"**HQ:** {prospect['hq']}")
            st.markdown(f"**Pain points:** {prospect['pain_points']}")
            st.markdown(f"**Use cases:** {prospect['use_cases']}")

        extra_context = st.text_area(
            "Additional context / talking points (optional)",
            placeholder="e.g. They recently had a breach. Decision-maker is the CISO. Competitor is Palo Alto SASE.",
            height=100,
        )

        generate_btn = st.button(
            "✉️ Generate Email",
            type="primary",
            use_container_width=True,
            disabled=not agent_endpoint,
        )

        if not agent_endpoint:
            st.warning("Enter the agent endpoint name in the sidebar to enable generation.")

    with col_right:
        st.subheader("Generated Email")

        if generate_btn and agent_endpoint:
            prompt_parts = [
                f"Email type: {email_type}",
                f"Target company: {prospect_name}",
                f"Industry: {prospect['industry']}",
                f"Company size: {prospect['size']}",
                f"Headquarters: {prospect['hq']}",
                f"Key pain points: {prospect['pain_points']}",
                f"Zscaler use cases for them: {prospect['use_cases']}",
            ]
            if extra_context.strip():
                prompt_parts.append(f"Additional context from the rep: {extra_context.strip()}")

            full_prompt = "\n".join(prompt_parts)

            with st.spinner("Generating email via AI Gateway…"):
                try:
                    email_text = call_agent(agent_endpoint, full_prompt)
                    st.session_state["last_email"] = email_text
                    st.session_state["last_prospect"] = prospect_name
                    st.session_state["last_email_type"] = email_type
                except Exception as e:
                    st.error(f"Agent call failed: {e}")

        if "last_email" in st.session_state:
            st.markdown(
                f"**{st.session_state['last_email_type']} → {st.session_state['last_prospect']}**"
            )
            st.text_area(
                "Email (editable)",
                value=st.session_state["last_email"],
                height=520,
                key="email_output",
            )
            st.download_button(
                "⬇️ Download .txt",
                data=st.session_state["last_email"],
                file_name=f"zscaler_{st.session_state['last_prospect'].lower().replace(' ', '_')}_{st.session_state['last_email_type'].lower().replace(' ', '_')}.txt",
                mime="text/plain",
            )
        else:
            st.info("Configure the prospect and email type on the left, then click **Generate Email**.")

# ===========================================================================
# TAB 2 — AI GATEWAY
# ===========================================================================

with tab_gateway:
    st.subheader("AI Gateway — Inference Table & Usage")
    st.caption(
        "AI Gateway logs every request and response to a Delta table in Unity Catalog. "
        "Use this view to monitor usage, latency, and rate-limit events."
    )

    # Derive table prefix from endpoint name (same logic as deploy_agent.py)
    if agent_endpoint:
        short_suffix = agent_endpoint.replace("zscaler-email-", "")
        inference_table = f"`{catalog}`.`{schema}`.`ai_gateway_{short_suffix}_payload`"
    else:
        short_suffix    = "<suffix>"
        inference_table = f"`{catalog}`.`{schema}`.`ai_gateway_<suffix>_payload`"

    st.info(
        f"Inference table: **{catalog}.{schema}.ai_gateway_{short_suffix}_payload**  \n"
        "This table is populated by AI Gateway and may take a few minutes to appear after the first request."
    )

    refresh = st.button("🔄 Refresh", disabled=not agent_endpoint)

    if refresh and agent_endpoint:
        try:
            df_gw = _query(
                f"""
                SELECT
                    DATE_TRUNC('minute', timestamp_ms / 1000) AS minute,
                    COUNT(*)                                   AS requests,
                    ROUND(AVG(execution_duration_ms), 0)       AS avg_latency_ms,
                    SUM(usage.completion_tokens)               AS completion_tokens
                FROM {inference_table}
                GROUP BY 1
                ORDER BY 1 DESC
                LIMIT 60
                """
            )
            if df_gw.empty:
                st.info("No data yet — generate some emails first.")
            else:
                import plotly.express as px

                st.subheader("Requests per Minute")
                fig = px.bar(
                    df_gw.sort_values("minute"),
                    x="minute",
                    y="requests",
                    labels={"minute": "Time", "requests": "Requests"},
                    color_discrete_sequence=["#00B2A9"],
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

                m1, m2, m3 = st.columns(3)
                m1.metric("Total Requests",    f"{df_gw['requests'].sum():,}")
                m2.metric("Avg Latency (ms)",  f"{df_gw['avg_latency_ms'].astype(float).mean():,.0f}")
                m3.metric("Completion Tokens", f"{df_gw['completion_tokens'].astype(float).sum():,.0f}")

                st.subheader("Raw Log (last 20 rows)")
                df_raw = _query(
                    f"""
                    SELECT
                        from_unixtime(timestamp_ms / 1000) AS timestamp,
                        request_id,
                        execution_duration_ms              AS latency_ms,
                        status_code,
                        usage.prompt_tokens,
                        usage.completion_tokens
                    FROM {inference_table}
                    ORDER BY timestamp_ms DESC
                    LIMIT 20
                    """
                )
                st.dataframe(df_raw, use_container_width=True, hide_index=True)

        except Exception as e:
            st.warning(
                f"Could not load inference table: {e}  \n"
                "The table is created after the first request through AI Gateway."
            )
    elif not agent_endpoint:
        st.info("Enter the agent endpoint name in the sidebar first.")
