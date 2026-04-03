"""
Zscaler Email Generator
Databricks Streamlit App — agent runs in-process, no Model Serving endpoint needed.
"""

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
# Agent — imported once, cached across reruns
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_agent():
    from agent_server.agent import generate_email
    return generate_email


generate_email = _get_agent()

# ---------------------------------------------------------------------------
# Prospect catalogue
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
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🔐 Zscaler Email Generator")
    st.markdown("---")
    st.caption("Agent runs in-process — powered by `databricks-claude-sonnet-4-5` via FMAPI.")

# ---------------------------------------------------------------------------
# App header
# ---------------------------------------------------------------------------

st.title("🔐 Zscaler Email Generator")
st.caption(
    "AI-powered sales outreach — select a prospect, choose an email type, "
    "and let the agent draft a personalised email."
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_generate, tab_arch = st.tabs(["✉️ Email Generator", "🏗️ Architecture"])

with tab_arch:
    st.subheader("Solution Architecture")
    st.caption("How the pieces fit together — from a single `databricks bundle deploy` to a running AI app.")

    st.graphviz_chart("""
        digraph architecture {
            graph [rankdir=LR, splines=ortho, nodesep=0.6, ranksep=1.0, bgcolor="#FAFAFA"]
            node  [shape=box, style="filled,rounded", fontname="Arial", fontsize=12, margin="0.3,0.15"]
            edge  [fontname="Arial", fontsize=10, color="#555555"]

            // ── DAB ──────────────────────────────────────────────────────
            subgraph cluster_dab {
                label       = "Databricks Asset Bundles"
                labeljust   = "l"
                style       = "dashed"
                color       = "#5C6BC0"
                fontname    = "Arial Bold"
                fontsize    = 12

                DAB [label="databricks.yml\\n+ resources/zscaler_app.yml", fillcolor="#E8EAF6", color="#5C6BC0"]
            }

            // ── Databricks App ───────────────────────────────────────────
            subgraph cluster_app {
                label       = "Databricks App  (zscaler-email-agent)"
                labeljust   = "l"
                style       = "filled"
                fillcolor   = "#F0FDF4"
                color       = "#16A34A"
                fontname    = "Arial Bold"
                fontsize    = 12

                UI    [label="Streamlit UI\\napp.py",                      fillcolor="#DBEAFE", color="#2563EB"]
                Agent [label="In-Process Agent\\nagent_server/agent.py\\nLangChain + ChatDatabricks", fillcolor="#D1FAE5", color="#059669"]
            }

            // ── External services ────────────────────────────────────────
            FMAPI   [label="Foundation Model API\\ndatabricks-claude-sonnet-4-5", fillcolor="#FEF9C3", color="#CA8A04"]
            Gateway [label="AI Gateway\\nRate limiting · Inference tables\\nUsage tracking",           fillcolor="#FFE4E6", color="#E11D48"]
            MLflow  [label="MLflow Tracing\\nautolog() → experiment",      fillcolor="#F3E8FF", color="#7C3AED"]

            // ── Edges ────────────────────────────────────────────────────
            DAB   -> UI      [label="deploys & versions", style=dashed, color="#5C6BC0"]
            UI    -> Agent   [label="calls in-process"]
            Agent -> Gateway [label="all LLM requests routed through"]
            Gateway -> FMAPI [label="proxies to FMAPI"]
            Agent -> MLflow  [label="traces every call", style=dashed, color="#7C3AED"]
        }
    """, use_container_width=True)

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("**🗂️ DAB**\nSingle `databricks bundle deploy` provisions the app. Config lives in git — no manual clicks.")
    col2.markdown("**📱 Databricks App**\nStreamlit UI + agent run in the same process. No separate Model Serving endpoint needed.")
    col3.markdown("**🔒 AI Gateway**\nSits between the agent and FMAPI — logs every request to a Delta table, enforces rate limits, tracks token usage.")
    col4.markdown("**🔍 MLflow Tracing**\n`mlflow.langchain.autolog()` captures every LLM call as a trace for debugging and evaluation.")

# ===========================================================================
# EMAIL GENERATOR
# ===========================================================================

with tab_generate:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Prospect & Email Settings")

        prospect_name = st.selectbox("Target Account", options=list(PROSPECTS.keys()))
        prospect      = PROSPECTS[prospect_name]
        email_type    = st.selectbox("Email Type", options=EMAIL_TYPES)

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

        generate_btn = st.button("✉️ Generate Email", type="primary", use_container_width=True)

    with col_right:
        st.subheader("Generated Email")

        if generate_btn:
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

            with st.spinner("Generating…"):
                try:
                    email_text = generate_email("\n".join(prompt_parts))
                    st.session_state["last_email"]      = email_text
                    st.session_state["last_prospect"]   = prospect_name
                    st.session_state["last_email_type"] = email_type
                except Exception as e:
                    st.error(f"Generation failed: {e}")

    if "last_email" in st.session_state:
        st.markdown(f"**{st.session_state['last_email_type']} → {st.session_state['last_prospect']}**")
        st.text_area(
            "Email (editable)",
            value=st.session_state["last_email"],
            height=520,
            key="email_output",
        )
        st.download_button(
            "⬇️ Download .txt",
            data=st.session_state["last_email"],
            file_name=(
                f"zscaler_{st.session_state['last_prospect'].lower().replace(' ', '_')}"
                f"_{st.session_state['last_email_type'].lower().replace(' ', '_')}.txt"
            ),
            mime="text/plain",
        )
    else:
        st.info("Configure the prospect and email type on the left, then click **Generate Email**.")
