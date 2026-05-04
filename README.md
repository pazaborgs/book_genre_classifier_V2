# 📚 Book Genre Classifier V2

> 🚧 **WORK IN PROGRESS:** Este projeto é um MVP funcional (v1.0), mas encontra-se em fase de refatoração ativa para otimização de chamadas de API (_Rate Limits_), economia de tokens e resiliência das ferramentas de web scraping.

Um sistema automatizado de classificação literária desenvolvido para o acervo e um colégio municipal.

O pipeline une Engenharia de Dados Clássica a Agentes Autônomos de IA para ler um inventário bruto, buscar sinopses na web e inferir a categoria pedagógica correta de cada livro, garantindo a idempotência do processamento.

## 🛠️ Stack Tecnológico

- **Engenharia de Dados:** Arquitetura Medallion (Bronze, Silver, Gold), Pandas, formato `.parquet`.
- **Agentes & IA:** LangGraph, LangChain, Google Gemini, Pydantic (Structured Outputs).
- **Integrações (Tools):** Google Books API, DuckDuckGo Search (Skoob / Goodreads).
- **Interface & Monitoramento:** Streamlit.

## 🚀 Como visualizar o painel de Logs (CLI Style)

Certifique-se de ter suas credenciais configuradas no arquivo `config.yaml` e no `.env` (não versionados por segurança).

```bash
# Inicie o painel de monitoramento
streamlit run app.py
```
