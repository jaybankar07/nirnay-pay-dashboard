import pytest
from app.models.merchant import Merchant


def test_merchant_isolation_cases_and_dashboard(client, db_session, seeded_merchant, seeded_case):
    # Create second merchant
    merchant_b = Merchant(id="merchant_b_999", name="Merchant B", email="b@merchant.com")
    db_session.add(merchant_b)
    db_session.commit()

    # Merchant B tries to access Merchant A's case -> MUST return 404
    res = client.get(f"/api/v1/recovery-cases/{seeded_case.id}?merchant_id={merchant_b.id}")
    assert res.status_code == 404
    assert res.json()["success"] is False

    # Merchant B tries to read Merchant A's audit trail -> MUST return 404
    audit_res = client.get(f"/api/v1/recovery-cases/{seeded_case.id}/audit?merchant_id={merchant_b.id}")
    assert audit_res.status_code == 404

    # Merchant B summary dashboard -> MUST report 0 cases & 0 revenue at risk
    dash_res = client.get(f"/api/v1/dashboard/summary?merchant_id={merchant_b.id}")
    assert dash_res.status_code == 200
    assert dash_res.json()["data"]["total_cases"] == 0
    assert dash_res.json()["data"]["revenue_at_risk_paise"] == 0
