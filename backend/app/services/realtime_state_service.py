from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock


@dataclass
class RealtimeViolationState:
    session_id: str
    camera_name: str
    violation_started_at: datetime | None = None
    last_violation_at: datetime | None = None
    last_alert_at: datetime | None = None


class RealtimeStateService:
    def __init__(self) -> None:
        self._states: dict[str, RealtimeViolationState] = {}
        self._lock = Lock()

    @staticmethod
    def _key(session_id: str, camera_name: str) -> str:
        return f"{session_id}:{camera_name}"

    def update(
        self,
        *,
        session_id: str,
        camera_name: str,
        has_violation: bool,
        observed_at: datetime,
        threshold_seconds: int,
        grace_seconds: int,
    ) -> dict:
        with self._lock:
            key = self._key(session_id, camera_name)
            state = self._states.get(key)
            if state is None:
                state = RealtimeViolationState(session_id=session_id, camera_name=camera_name)
                self._states[key] = state

            if has_violation:
                gap_too_long = (
                    state.last_violation_at is not None
                    and observed_at - state.last_violation_at > timedelta(seconds=grace_seconds)
                )
                if state.violation_started_at is None or gap_too_long:
                    state.violation_started_at = observed_at
                state.last_violation_at = observed_at
            else:
                if state.last_violation_at and observed_at - state.last_violation_at > timedelta(seconds=grace_seconds):
                    state.violation_started_at = None
                    state.last_violation_at = None

            active_seconds = 0.0
            if has_violation and state.violation_started_at is not None:
                active_seconds = max(0.0, (observed_at - state.violation_started_at).total_seconds())
            elif (
                not has_violation
                and state.violation_started_at is not None
                and state.last_violation_at is not None
                and observed_at - state.last_violation_at <= timedelta(seconds=grace_seconds)
            ):
                active_seconds = max(0.0, (state.last_violation_at - state.violation_started_at).total_seconds())

            alert_armed = has_violation and active_seconds >= threshold_seconds
            if alert_armed:
                state.last_alert_at = observed_at

            return {
                "current_violation": has_violation,
                "active_violation_seconds": round(active_seconds, 2),
                "threshold_seconds": threshold_seconds,
                "alert_armed": alert_armed,
                "within_grace_period": (
                    not has_violation
                    and state.last_violation_at is not None
                    and observed_at - state.last_violation_at <= timedelta(seconds=grace_seconds)
                ),
            }

    def clear(self, session_id: str, camera_name: str) -> None:
        with self._lock:
            self._states.pop(self._key(session_id, camera_name), None)


realtime_state_service = RealtimeStateService()
