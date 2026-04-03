"""
Deploy the Zscaler Email Agent to a Model Serving endpoint and configure
AI Gateway (inference tables + rate limiting + usage tracking).

Usage (via DAB job task):
    python deploy_agent.py <catalog> <schema>
"""

import sys
import time

import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
)

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

CATALOG = sys.argv[1] if len(sys.argv) > 1 else "main"
SCHEMA  = sys.argv[2] if len(sys.argv) > 2 else "zscaler"

_w  = WorkspaceClient()
_me = _w.current_user.me()
_short = "".join(c for c in (_me.user_name or "").split("@")[0] if c.isalnum())[:8]

MODEL_NAME    = f"{CATALOG}.{SCHEMA}.zscaler_email_agent_{_short}"
ENDPOINT_NAME = f"zscaler-email-{_short}"

# ---------------------------------------------------------------------------
# Resolve latest model version
# ---------------------------------------------------------------------------

versions = _w.registered_models.list_versions(MODEL_NAME)
latest   = max(versions, key=lambda v: int(v.version))
MODEL_VERSION = str(latest.version)
print(f"Deploying {MODEL_NAME} version {MODEL_VERSION} → {ENDPOINT_NAME}")

# ---------------------------------------------------------------------------
# Create or update serving endpoint
# ---------------------------------------------------------------------------

served_entity = ServedEntityInput(
    entity_name=MODEL_NAME,
    entity_version=MODEL_VERSION,
    scale_to_zero_enabled=True,
    workload_size="Small",
)

config = EndpointCoreConfigInput(served_entities=[served_entity])

existing = {e.name for e in _w.serving_endpoints.list()}

if ENDPOINT_NAME in existing:
    print(f"Updating existing endpoint: {ENDPOINT_NAME}")
    _w.serving_endpoints.update_config(name=ENDPOINT_NAME, served_entities=[served_entity])
else:
    print(f"Creating new endpoint: {ENDPOINT_NAME}")
    _w.serving_endpoints.create(name=ENDPOINT_NAME, config=config)

# ---------------------------------------------------------------------------
# Wait for endpoint to reach READY state
# ---------------------------------------------------------------------------

print("Waiting for endpoint to become READY (this can take ~10-15 min)...")
for attempt in range(90):
    status = _w.serving_endpoints.get(ENDPOINT_NAME)
    state  = status.state.config_update if status.state else None
    ready  = getattr(status.state, "ready", None)
    print(f"  [{attempt * 10}s] config_update={state}, ready={ready}")
    if str(ready) == "READY":
        break
    time.sleep(10)
else:
    print("WARNING: endpoint did not reach READY state within timeout.")

# ---------------------------------------------------------------------------
# Configure AI Gateway
# ---------------------------------------------------------------------------

host  = _w.config.host.rstrip("/")
token = _w.config.token or ""

# Prefer injected token (running in serverless job context)
import os
token = os.environ.get("DATABRICKS_TOKEN", token)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type":  "application/json",
}

gateway_config = {
    "inference_table_config": {
        "enabled":           True,
        "catalog_name":      CATALOG,
        "schema_name":       SCHEMA,
        "table_name_prefix": f"ai_gateway_{_short}",
    },
    "rate_limits": [
        {
            "calls":          60,
            "renewal_period": "minute",
            "key":            "endpoint",
        }
    ],
    "usage_tracking_config": {
        "enabled": True,
    },
}

r = requests.put(
    f"{host}/api/2.0/serving-endpoints/{ENDPOINT_NAME}/ai-gateway",
    json=gateway_config,
    headers=headers,
    timeout=30,
)

if r.ok:
    print("AI Gateway configured:")
    print(f"  Inference tables : {CATALOG}.{SCHEMA}.ai_gateway_{_short}_*")
    print(f"  Rate limit       : 60 calls / minute")
    print(f"  Usage tracking   : enabled")
else:
    print(f"WARNING: AI Gateway config returned {r.status_code}: {r.text}")

# ---------------------------------------------------------------------------
# Print summary for the app operator
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print(f"ENDPOINT NAME  : {ENDPOINT_NAME}")
print(f"MODEL          : {MODEL_NAME} v{MODEL_VERSION}")
print(f"CATALOG.SCHEMA : {CATALOG}.{SCHEMA}")
print("Copy the endpoint name above into the app sidebar.")
print("=" * 60)
