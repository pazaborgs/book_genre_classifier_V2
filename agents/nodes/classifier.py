import time
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.schemas import ClassificationOutput
from agents.prompts import CLASSIFIER_PROMPT


def classifier_agent(state: dict) -> dict:
    """
    Nó 2: Analisa a sinopse bruta e extrai os dados estruturados via LLM.
    """

    title = state.get("title", "Título Desconhecido")
    searched_synopsis = state.get("searched_synopsis", "")
    tries = state.get("retry_count", 0)

    print(f"\n  [*] Processando inteligência: '{title}'")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.2,
    )

    structured_llm = llm.with_structured_output(ClassificationOutput)

    input_text = f"{CLASSIFIER_PROMPT}\n\nDADOS DO LIVRO:\nTítulo: {title}\nSinopse Bruta: {searched_synopsis}"

    try:
        res = structured_llm.invoke(input_text)

        if res.color_suggestion == "BRANCO" or res.color_suggestion == "ERRO":
            print(
                f"  └─ [AVISO] IA retornou cor genérica '{res.color_suggestion}'. Contabilizando falha."
            )
            new_retry = tries + 1
        else:
            print(f"  └─ [SUCESSO] Classificação definida: {res.color_suggestion}")
            new_retry = tries

        return {
            "color_suggestion": res.color_suggestion,
            "justification": res.justification,
            "final_synopsis": res.final_synopsis,
            "final_tags": res.final_tags,
            "top_3_probabilities": [
                prob.model_dump() for prob in res.top_3_probabilities
            ],
            "retry_count": new_retry,
        }

    except Exception as e:
        erro_str = str(e)

        print(f"  [!] Falha na inferência (Tentativa {tries + 1})")
        print(f"      Detalhes: {erro_str[:150]}...\n")

        # Lidando com erro de cota

        if "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str:
            print(f"  [AVISO] Limite de velocidade do Gemini (Free Tier) atingido.")
            print(
                f"  [PAUSA] Congelando a esteira por 60 segundos para resfriar a API..."
            )
            time.sleep(60)
            print(f"  [RETOMANDO] Repouso finalizado. Devolvendo para o roteador...")

        return {
            "color_suggestion": "ERRO",
            "justification": f"Falha na API: {erro_str[:100]}",
            "top_3_probabilities": [],
            "retry_count": tries + 1,
        }
