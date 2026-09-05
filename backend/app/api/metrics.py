"""
Metrics & SLO API Router for Nirnay Pay (RecoveryOS).
Exposes Prometheus operational metrics and SLO status endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.slo_service import SLOService

router = APIRouter(prefix="/metrics", tags=["Metrics & Observability"])


@router.get("")
def get_metrics(db: Session = Depends(get_db)):
    """Returns platform operational metrics and SLO measurements."""
    slo = SLOService(db)
    metrics_data = slo.compute_slo_metrics()

    # Format Prometheus plain text metric response
    prom_lines = [
        "# HELP nirnay_reconciliation_accuracy_pct Financial reconciliation accuracy percentage",
        "# TYPE nirnay_reconciliation_accuracy_pct gauge",
        f"nirnay_reconciliation_accuracy_pct {metrics_data['sli_reconciliation_accuracy_pct']}",
        "# HELP nirnay_dlq_count Dead-letter queue event count",
        "# TYPE nirnay_dlq_count counter",
        f"nirnay_dlq_count {metrics_data['dlq_count']}",
        "# HELP nirnay_ledger_total Total financial ledger entry count",
        "# TYPE nirnay_ledger_total counter",
        f"nirnay_ledger_total {metrics_data['total_ledger_entries']}"
    ]

    return {
        "success": True,
        "data": metrics_data,
        "prometheus_format": "\n".join(prom_lines)
    }
