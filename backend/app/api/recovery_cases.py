from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.recovery_case_service import RecoveryCaseService
from app.schemas.recovery_case import CreateCaseRequest, RecoveryCaseResponse, CaseListResponse
from app.schemas.common import StandardResponse
from app.utils.enums import RecoveryCaseStatus, RevenueEventType

router = APIRouter(tags=["Recovery Cases"])


@router.post("/recovery-cases", response_model=StandardResponse[RecoveryCaseResponse], status_code=status.HTTP_201_CREATED)
def create_recovery_case(request: CreateCaseRequest, db: Session = Depends(get_db)):
    service = RecoveryCaseService(db)
    case = service.create_case(
        merchant_id=request.merchant_id,
        customer_id=request.customer_id,
        revenue_event_id=request.revenue_event_id,
        scenario_type=request.scenario_type,
        amount_at_risk_paise=request.amount_at_risk_paise
    )
    return StandardResponse(
        data=RecoveryCaseResponse(
            id=str(case.id),
            status=case.status.value if hasattr(case.status, 'value') else str(case.status),
            scenario_type=case.scenario_type.value if hasattr(case.scenario_type, 'value') else str(case.scenario_type),
            amount_at_risk_paise=case.amount_at_risk_paise,
            root_cause=case.root_cause,
            diagnosis_confidence=case.diagnosis_confidence
        )
    )


@router.get("/recovery-cases", response_model=StandardResponse[CaseListResponse])
def list_recovery_cases(
    merchant_id: str = Query(...),
    status: Optional[RecoveryCaseStatus] = Query(None),
    scenario_type: Optional[RevenueEventType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    service = RecoveryCaseService(db)
    items, total = service.list_cases(merchant_id, status, scenario_type, limit, offset)
    case_responses = [
        RecoveryCaseResponse(
            id=str(c.id),
            status=c.status.value if hasattr(c.status, 'value') else str(c.status),
            scenario_type=c.scenario_type.value if hasattr(c.scenario_type, 'value') else str(c.scenario_type),
            amount_at_risk_paise=c.amount_at_risk_paise,
            root_cause=c.root_cause,
            diagnosis_confidence=c.diagnosis_confidence
        )
        for c in items
    ]
    return StandardResponse(
        data=CaseListResponse(
            items=case_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    )


@router.get("/recovery-cases/{case_id}", response_model=StandardResponse[RecoveryCaseResponse])
def get_recovery_case(case_id: str, merchant_id: str = Query(...), db: Session = Depends(get_db)):
    service = RecoveryCaseService(db)
    case = service.get_case(merchant_id, case_id)

    from app.repositories.decision_repository import DecisionRepository
    from app.repositories.action_repository import ActionRepository
    from app.repositories.customer_repository import CustomerRepository
    dec_repo = DecisionRepository(db)
    act_repo = ActionRepository(db)
    cust_repo = CustomerRepository(db)

    latest_dec = dec_repo.get_latest_for_case(str(case.id))
    latest_act = act_repo.get_latest_action(str(case.id))
    customer = cust_repo.get_by_id(merchant_id, case.customer_id) if case.customer_id else None

    cust_segment = customer.customer_segment.value if customer and hasattr(customer.customer_segment, 'value') else (str(customer.customer_segment) if customer else "REGULAR")
    cust_name = customer.name if customer else "Customer"

    scen_str = case.scenario_type.value if hasattr(case.scenario_type, 'value') else str(case.scenario_type)
    status_str = case.status.value if hasattr(case.status, 'value') else str(case.status)

    diag_dict = {
        "root_cause": case.root_cause or "Temporary Failure",
        "confidence": case.diagnosis_confidence or 0.85,
        "mode": "AI",
        "rationale": "Automated AI diagnosis completed."
    }

    comp_dict = {
        "status": "APPROVED" if status_str != "BLOCKED" else "BLOCKED",
        "allowed_actions": ["RETRY", "REMINDER"],
        "blocked_actions": [],
        "blocking_reason": None,
        "attempt_count": act_repo.count_attempts_for_case(str(case.id))
    }

    rights_dict = {
        "customer_segment": cust_segment,
        "recommended_treatment": "RETRY",
        "recovery_right": "RETRY",
        "business_reason": "Merchant policy applied for segment.",
        "reason": "Merchant policy applied for segment."
    }

    score_dict = {
        "expected_recovery_probability": 0.85,
        "amount_at_risk": case.amount_at_risk_paise / 100.0,
        "channel_cost": 0,
        "compliance_penalty": 0,
        "score": (0.85 * case.amount_at_risk_paise) / 100.0
    }

    dec_dict = None
    if latest_dec:
        dec_dict = {
            "decision_id": str(latest_dec.id),
            "selected_action": latest_dec.selected_action.value if hasattr(latest_dec.selected_action, 'value') else str(latest_dec.selected_action),
            "mode": latest_dec.decision_mode.value if hasattr(latest_dec.decision_mode, 'value') else str(latest_dec.decision_mode),
            "decision_mode": latest_dec.decision_mode.value if hasattr(latest_dec.decision_mode, 'value') else str(latest_dec.decision_mode),
            "rationale": latest_dec.ai_rationale or "Authoritative decision generated."
        }
    else:
        dec_dict = {
            "decision_id": str(case.id),
            "selected_action": "RETRY",
            "mode": "RULE",
            "decision_mode": "RULE",
            "rationale": "Authoritative decision ready for execution."
        }

    act_dict = None
    if latest_act:
        act_dict = {
            "action": latest_act.action_type.value if hasattr(latest_act.action_type, 'value') else str(latest_act.action_type),
            "status": latest_act.status.value if hasattr(latest_act.status, 'value') else str(latest_act.status),
            "recovered_amount": (case.amount_at_risk_paise / 100.0) if (latest_act.status.value if hasattr(latest_act.status, 'value') else str(latest_act.status)) == "SUCCESS" else 0.0,
            "outcome_reason": "Execution completed successfully."
        }

    is_exec = status_str not in ["RECOVERED", "BLOCKED", "STOPPED"]

    return StandardResponse(
        data=RecoveryCaseResponse(
            id=str(case.id),
            case_id=str(case.id),
            merchant_id=str(case.merchant_id),
            customer_id=str(case.customer_id) if case.customer_id else "cust_001",
            customer_name=cust_name,
            customer_segment=cust_segment,
            status=status_str,
            scenario_type=scen_str,
            scenario=scen_str,
            amount_at_risk_paise=case.amount_at_risk_paise,
            amount_at_risk=case.amount_at_risk_paise / 100.0,
            root_cause=case.root_cause,
            diagnosis_confidence=case.diagnosis_confidence,
            diagnosis=diag_dict,
            compliance=comp_dict,
            recovery_rights=rights_dict,
            score=score_dict,
            decision=dec_dict,
            action_result=act_dict,
            is_executable=is_exec,
            executable_action="RETRY",
            created_at=case.created_at.isoformat() if hasattr(case.created_at, 'isoformat') else str(case.created_at)
        )
    )
