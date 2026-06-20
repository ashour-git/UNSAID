import time
from collections import defaultdict


class FailedLoginTracker:
    def __init__(self) -> None:
        self._failures: dict[tuple[str, str], list[float]] = defaultdict(list)

    def record_failure(self, email: str, ip: str) -> None:
        now = time.time()
        key = (email.lower(), ip)
        self._failures[key].append(now)
        cutoff = now - 15 * 60
        self._failures[key] = [t for t in self._failures[key] if t > cutoff]

    def is_locked_out(self, email: str, ip: str) -> bool:
        now = time.time()
        key = (email.lower(), ip)
        timestamps = self._failures.get(key, [])
        cutoff = now - 15 * 60
        recent = [t for t in timestamps if t > cutoff]
        self._failures[key] = recent
        if len(recent) < 5:
            return False
        lockout_start = sorted(recent)[4]
        return (now - lockout_start) < 30 * 60

    def reset(self, email: str, ip: str) -> None:
        key = (email.lower(), ip)
        self._failures.pop(key, None)


failed_login_tracker = FailedLoginTracker()