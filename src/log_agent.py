"""
Log and register the Zscaler Email Agent in Unity Catalog.

Usage (via DAB job task):
    python log_agent.py <catalog> <schema>
"""

import inspect
import os
import sys

import mlflow
from databricks.sdk import WorkspaceClient

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

CATALOG = sys.argv[1] if len(sys.argv) > 1 else "main"
SCHEMA  = sys.argv[2] if len(sys.argv) > 2 else "zscaler"

# Derive a short user suffix for the model name to avoid collisions in
# shared workspaces (same pattern as claro-bundle).
_w  = WorkspaceClient()
_me = _w.current_user.me()
_short = "".join(c for c in (_me.user_name or "").split("@")[0] if c.isalnum())[:8]

MODEL_NAME    = f"{CATALOG}.{SCHEMA}.zscaler_email_agent_{_short}"
EXPERIMENT    = f"/Users/{_me.user_name}/zscaler-email-agent"

# ---------------------------------------------------------------------------
# Resolve agent.py path — __file__ unavailable in serverless spark_python_task
# ---------------------------------------------------------------------------

_HERE      = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
AGENT_PATH = os.path.join(_HERE, "agent.py")

# ---------------------------------------------------------------------------
# Ensure schema exists
# ---------------------------------------------------------------------------

try:
    _w.schemas.create(catalog_name=CATALOG, name=SCHEMA)
    print(f"Created schema {CATALOG}.{SCHEMA}")
except Exception:
    print(f"Schema {CATALOG}.{SCHEMA} already exists — OK")

# ---------------------------------------------------------------------------
# Log and register
# ---------------------------------------------------------------------------

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(EXPERIMENT)

with mlflow.start_run(run_name="log_zscaler_email_agent"):
    logged = mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=AGENT_PATH,
        pip_requirements=[
            "mlflow>=2.14.0",
            "databricks-sdk>=0.20.0",
            "requests>=2.31.0",
        ],
        registered_model_name=MODEL_NAME,
    )

print(f"Registered model : {MODEL_NAME}")
print(f"Model URI        : {logged.model_uri}")
print(f"Short suffix     : {_short}")
print(f"Endpoint name    : zscaler-email-{_short}")
