import time


class _RateLimiter:
    def __init__(self, min_gap_seconds: float = 6.0):
        """
        Garante um intervalo mínimo entre chamadas.
        6s entre chamadas = 10 chamadas/minuto
        """
        self.min_gap = min_gap_seconds
        self._last_call: float = 0.0

    def wait_if_needed(self):
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self.min_gap:
            sleep_for = self.min_gap - elapsed
            print(
                f"  └─ [THROTTLE] Aguardando {sleep_for:.1f}s (gap mínimo entre chamadas)..."
            )
            time.sleep(sleep_for)
        self._last_call = time.time()


limiter = _RateLimiter(min_gap_seconds=6.0)
