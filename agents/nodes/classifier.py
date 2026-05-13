import time
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.schemas import ClassificationOutput
from agents.prompts import CLASSIFIER_PROMPT
from agents._limiter_state import limiter as _limiter

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.2,
)
_structured_llm = _llm.with_structured_output(ClassificationOutput)


# ---------------------------------------------------------------------------
# AGENTE CLASSIFICADOR
# ---------------------------------------------------------------------------


def classifier_agent(state: dict) -> dict:
    """
    Nó 2: Analisa a sinopse bruta e extrai dados estruturados via LLM.

    Retornos possíveis:
      - Cor específica (VERDE, AZUL, etc.)  -> sucesso, nao incrementa retry
      - BRANCO  -> classificacao generica valida, incrementa retry para nova tentativa
      - ERRO    -> falha tecnica, incrementa retry, nao deve ser salvo como final
    """

    title = state.get("title", "Titulo Desconhecido")
    searched_synopsis = state.get("searched_synopsis", "")
    tries = state.get("retry_count", 0)

    print(f"\n  [*] Classificando: '{title}' (tentativa {tries + 1})")

    input_text = (
        f"{CLASSIFIER_PROMPT}\n\n"
        f"DADOS DO LIVRO:\nTitulo: {title}\nSinopse Bruta: {searched_synopsis}"
    )

    for attempt in range(3):
        try:
            _limiter.wait_if_needed()
            print(f"  └─ [INVOKE] {time.strftime('%H:%M:%S')}")
            res = _structured_llm.invoke(input_text)

            is_error = res.color_suggestion == "ERRO"
            is_white = res.color_suggestion == "BRANCO"

            if is_error:
                print(f"  └─ [AVISO] Modelo retornou ERRO. Contabilizando falha.")
            elif is_white:
                print(f"  └─ [AVISO] BRANCO (generico). Contabilizando para retry.")
            else:
                print(f"  └─ [SUCESSO] Cor: {res.color_suggestion}")

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
            is_daily_quota = (
                "quota" in err.lower() or "DAILY" in err or "exhausted" in err.lower()
            )

            # Se for rate_limit, aguarda e "invoke" novamente

            if is_rate_limit:

                if is_daily_quota:
                    print("  └─ [!] Cota diária esgotada. Abortando sessão.")
                    raise RuntimeError("DAILY_QUOTA_EXHAUSTED")

                wait = 90 + (attempt * 60)
                print(
                    f"  └─ [RATE LIMIT] Tentativa {attempt + 1}/3. Pausando {wait}s..."
                )
                if attempt == 2:
                    print(
                        "  └─ [!] Rate limit persistente apos 3 tentativas. Abortando."
                    )
                    break
                time.sleep(wait)
                continue

            print(f"  └─ [!] Erro de inferencia: {err[:200]}")
            break

    return {
        "color_suggestion": "ERRO",
        "justification": "Falha tecnica apos multiplas tentativas.",
        "final_synopsis": "Classificacao abortada.",
        "final_tags": [],
        "top_3_probabilities": [],
        "retry_count": tries + 1,
    }
