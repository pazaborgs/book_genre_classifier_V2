# 📚 Book Genre Classifier V2

> 🚧 **WORK IN PROGRESS:** Este projeto encontra-se em fase de refatoração ativa para otimização de chamadas de API (_Rate Limits_), economia de tokens, resiliência das ferramentas de web scraping...

Um sistema automatizado de classificação de gênero literário desenvolvido para o acervo de um colégio municipal.

O pipeline une Engenharia de Dados Clássica a Agentes Autônomos de IA para ler um inventário bruto, buscar sinopses na web e inferir a categoria (gênero) correta de cada livro, garantindo a idempotência do processamento.

## 🛠️ Stack (Planejado)

- **Engenharia de Dados:** Arquitetura Medallion (Bronze, Silver, Gold), Pandas, formato `.parquet`.
- **Agentes & IA:** LangGraph, LangChain, Google Gemini, Pydantic (Structured Outputs).
- **Integrações (Tools):** Google Books API, DuckDuckGo Search (Skoob / Goodreads).
- **Interface & Monitoramento:** Streamlit.

## 📌 Backlog

[] Colocar os dados na nuvem (GCP, AWS…) + container Docker.
[] Criar o painel interativo usando Streamlit.
[] Melhorar o prompt de classificação e testar modelos de LLM diferentes.
[] Classificar 20-30% da base de dados até o final do mês.

