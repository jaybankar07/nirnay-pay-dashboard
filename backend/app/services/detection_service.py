import uuid
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.revenue_event import RevenueEvent
from app.models.recovery_case import RecoveryCase
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.repositories.merchant_repository import MerchantRepository
from app.services.audit_service import AuditService
from app.utils.enums import RevenueEventType, RecoveryCaseStatus, AuditEventType, ActorType
from app.core.exceptions import NotFoundError, ValidationError


class DetectionService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.merchant_repo = MerchantRepository(db)
        self.audit_service = AuditService(db)

    def detect_event(
        self,
        merchant_id: str,
        customer_id: Optional[str],
        event_type: RevenueEventType,
        amount_paise: int,
        reason_code: Optional[str] = None,
        occurred_at: Optional[Any] = None
    ) -> Tuple[RevenueEvent, RecoveryCase]:
        # Validate merchant exists
        merchant = self.merchant_repo.get_by_id(merchant_id)
        if not merchant:
            raise NotFoundError(f"Merchant '{merchant_id}' not found.")

        if amount_paise < 0:
            raise ValidationError("Revenue event amount cannot be negative.")

        # Ensure customer_id is a valid UUID
        valid_cust_id = None
        if customer_id:
            try:
                valid_cust_id = str(uuid.UUID(customer_id))
            except (ValueError, TypeError):
                valid_cust_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(customer_id)))

        if valid_cust_id:
            customer_id = valid_cust_id
            from app.models.customer import Customer
            existing_cust = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not existing_cust:
                new_cust = Customer(
                    id=customer_id,
                    merchant_id=merchant_id,
                    external_customer_id=f"ext_{str(customer_id)[:8]}",
                    name=f"Customer {str(customer_id)[:8]}",
                    customer_segment="FIRST_TIME"
                )
                self.db.add(new_cust)
                self.db.commit()

        # Create Revenue Event
        event = RevenueEvent(
            merchant_id=merchant_id,
            customer_id=customer_id,
            event_type=event_type,
            amount_paise=amount_paise,
            reason_code=reason_code,
            occurred_at=occurred_at
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Create Recovery Case
        case = RecoveryCase(
            merchant_id=merchant_id,
            customer_id=customer_id,
            revenue_event_id=event.id,
            status=RecoveryCaseStatus.DETECTED,
            scenario_type=event_type,
            amount_at_risk_paise=amount_paise
        )
        created_case = self.case_repo.create(case)

        # Audit Log
        self.audit_service.log_event(
            case_id=str(created_case.id),
            event_type=AuditEventType.CASE_DETECTED,
            actor_type=ActorType.SYSTEM,
            event_data={
                "merchant_id": merchant_id,
                "event_id": str(event.id),
                "scenario_type": event_type.value if hasattr(event_type, 'value') else str(event_type),
                "amount_at_risk_paise": amount_paise
            }
        )

        return event, created_case
