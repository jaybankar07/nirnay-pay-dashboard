import pytest
from app.main import app

DOCUMENTED_ENDPOINTS = {
    ("/api/v1/health", "GET"),
    ("/api/v1/merchants/{merchant_id}", "GET"),
    ("/api/v1/recovery-cases", "POST"),
    ("/api/v1/recovery-cases", "GET"),
    ("/api/v1/recovery-cases/{case_id}", "GET"),
    ("/api/v1/detect", "POST"),
    ("/api/v1/recovery-cases/{case_id}/diagnose", "POST"),
    ("/api/v1/recovery-cases/{case_id}/compliance-check", "POST"),
    ("/api/v1/recovery-cases/{case_id}/recovery-rights", "POST"),
    ("/api/v1/recovery-cases/{case_id}/score", "POST"),
    ("/api/v1/recovery-cases/{case_id}/decide", "POST"),
    ("/api/v1/recovery-cases/{case_id}/execute", "POST"),
    ("/api/v1/recovery-cases/{case_id}/audit", "GET"),
    ("/api/v1/dashboard/summary", "GET"),
    ("/api/v1/dashboard/cases", "GET"),
    ("/api/v1/batch-runs", "POST"),
    ("/api/v1/evaluation/run", "POST"),
    ("/api/v1/metrics", "GET"),
    ("/api/v1/readiness", "GET"),
    ("/api/v1/admin/kill-switch", "GET"),
    ("/api/v1/admin/kill-switch", "POST"),
}



def test_api_contract_matches_specification(client):
    """
    Contract Test: Verifies that the FastAPI OpenAPI schema exposes ONLY
    documented public endpoints as specified in Nirnay_Pay_API_Specification_v1.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()

    actual_endpoints = set()
    for path, methods in openapi.get("paths", {}).items():
        for method in methods.keys():
            actual_endpoints.add((path, method.upper()))

    # Ensure every documented endpoint is implemented
    missing_endpoints = DOCUMENTED_ENDPOINTS - actual_endpoints
    assert not missing_endpoints, f"Missing documented public endpoints: {missing_endpoints}"

    # Ensure no undocumented public endpoints exist under /api/v1
    undocumented = {ep for ep in actual_endpoints if ep[0].startswith("/api/v1") and ep not in DOCUMENTED_ENDPOINTS}
    assert not undocumented, f"Undocumented public endpoints detected: {undocumented}"
