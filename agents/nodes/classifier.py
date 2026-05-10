import time
from collections import deque
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.schemas import ClassificationOutput
from agents.prompts import CLASSIFIER_PROMPT

# Rate Limiter


class _RateLimiter:
    def __init__(self, rpm: int = 8):
        self.rpm = rpm
        self._timestamps: deque = deque()

    def wait_if_needed(self):
        now = time.time()
        while self._timestamps and now - self._timestamps[0] > 60:
            self._timestamps.popleft()

        if len(self._timestamps) >= self.rpm:
            sleep_for = 61 - (now - self._timestamps[0])
            print(f"  └─ [THROTTLE] Janela cheia. Aguardando {sleep_for:.1f}s...")
            time.sleep(sleep_for)

        self._timestamps.append(time.time())


_limiter = _RateLimiter(rpm=8)

# LLM instanciado

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.2,
)
_structured_llm = _llm.with_structured_output(ClassificationOutput)


def classifier_agent(state: dict) -> dict:
    """
    Nó 2: Analisa a sinopse bruta e extrai dados estruturados via LLM.
    """
    title = state.get("title", "Título Desconhecido")
    searched_synopsis = state.get("searched_synopsis", "")
    tries = state.get("retry_count", 0)

    print(f"\n  [*] Classificando: '{title}'")

    input_text = (
        f"{CLASSIFIER_PROMPT}\n\n"
        f"DADOS DO LIVRO:\nTítulo: {title}\nSinopse Bruta: {searched_synopsis}"
    )

    for attempt in range(3):
        try:
            _limiter.wait_if_needed()  # Throttle preventivo
            res = _structured_llm.invoke(input_text)

            is_error = res.color_suggestion == "ERRO"
            is_white = res.color_suggestion == "BRANCO"

            if is_error:
                print(f"  └─ [AVISO] Modelo retornou ERRO. Contabilizando falha.")
            elif is_white:
                print(
                    f"  └─ [AVISO] Classificado como BRANCO (genérico). Contabilizando para retry."
                )
            else:
                print(f"  └─ [SUCESSO] Cor definida: {res.color_suggestion}")

            return {
                "color_suggestion": res.color_suggestion,
                "justification": res.justification,
                "final_synopsis": res.final_synopsis,
                "final_tags": res.final_tags,
                "top_3_probabilities": [
                    p.model_dump() for p in res.top_3_probabilities
                ],
                "retry_count": tries + (1 if (is_error or is_white) else 0),
            }

        except Exception as e:
            err = str(e)
            is_rate_limit = "429" in err or "RESOURCE_EXHAUSTED" in err

            if is_rate_limit:
                wait = 60 * (attempt + 1)  # 60s → 120s → 180s
                print(
                    f"  └─ [RATE LIMIT] Tentativa {attempt + 1}/3. Pausando {wait}s..."
                )

                if attempt == 2:
                    print("  └─ [!] Rate limit persistente após 3 tentativas.")
                    break

                time.sleep(wait)
                continue

            print(f"  └─ [!] Erro de inferência: {err[:150]}")
            break

    return {
        "color_suggestion": "ERRO",
        "justification": "Falha técnica após múltiplas tentativas.",
        "final_synopsis": "Classificação abortada.",
        "final_tags": [],
        "top_3_probabilities": [],
        "retry_count": tries + 1,
    }
