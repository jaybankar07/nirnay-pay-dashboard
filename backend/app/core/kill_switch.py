"""
Emergency Kill Switch Module for Nirnay Pay (RecoveryOS).
Provides instant circuit-breaker controls for financial execution safety.
"""
import threading
from typing import Dict, Set, Tuple, Any


class KillSwitchState:
    _global_stop: bool = False
    _stopped_tenants: Set[str] = set()
    _stopped_scenarios: Set[str] = set()
    _lock = threading.Lock()

    @classmethod
    def set_global_stop(cls, stop: bool) -> None:
        with cls._lock:
            cls._global_stop = stop

    @classmethod
    def set_tenant_stop(cls, tenant_id: str, stop: bool) -> None:
        with cls._lock:
            if stop:
                cls._stopped_tenants.add(tenant_id)
            else:
                cls._stopped_tenants.discard(tenant_id)

    @classmethod
    def set_scenario_stop(cls, scenario: str, stop: bool) -> None:
        with cls._lock:
            if stop:
                cls._stopped_scenarios.add(scenario)
            else:
                cls._stopped_scenarios.discard(scenario)

    @classmethod
    def is_execution_allowed(cls, tenant_id: str = None, scenario: str = None) -> Tuple[bool, str]:
        """Checks if recovery execution is permitted under current kill switch controls."""
        with cls._lock:
            if cls._global_stop:
                return False, "Global emergency recovery stop active (GLOBAL_RECOVERY_STOP)."
            if tenant_id and tenant_id in cls._stopped_tenants:
                return False, f"Recovery execution stopped for merchant {tenant_id} (TENANT_RECOVERY_STOP)."
            if scenario and scenario in cls._stopped_scenarios:
                return False, f"Recovery execution stopped for scenario {scenario} (SCENARIO_RECOVERY_STOP)."
            return True, "ALLOWED"

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        with cls._lock:
            return {
                "global_stop": cls._global_stop,
                "stopped_tenants": list(cls._stopped_tenants),
                "stopped_scenarios": list(cls._stopped_scenarios)
            }
