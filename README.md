# 📚 BOOK GENRE CLASSIFIER V2

> ⚡ **STATUS:** Em produção (WIP)

> 🔗 **DEMO:** [Acesse o Painel](https://bookgenreclassifierv2-b3zq5g7tfrpedupkxvixux.streamlit.app/)

Sistema automatizado de classificação de gênero literário desenvolvido para o acervo de um colégio municipal.

O pipeline une Engenharia de Dados e Agentes Autônomos de IA para processar inventários brutos, buscar sinopses na web e inferir categorias literárias com garantia de idempotência.

## 🏗️ Arquitetura e Engenharia

- **Engine de IA:** Agentes autônomos via LangGraph e Gemini 2.5 Flash-Lite com saídas estruturadas (Pydantic).
- **Resiliência:** Rate Limiting customizado (20 RPM) com lógica Anti-Burst para otimização de APIs gratuitas.
- **Infraestrutura:** Containerização via Docker com gerenciamento de pacotes ultra-rápido via `uv`.
- **Camada de Dados:** Arquitetura Medallion (Bronze/Silver/Gold) persistida em arquivos `.parquet`.

## 🛠️ Tecnologias

- **Inteligência Artificial:** LangGraph, LangChain, Google Gemini (2.5 Flash-Lite) e Pydantic (Structured Outputs).
- **Engenharia de Dados:** Pandas, formato `.parquet` e Arquitetura Medallion.
- **Infraestrutura e Deploy:** Docker, `uv` (Package Manager) e Streamlit.

## 📌 Milestones

- [x] Arquitetura de camadas (Medallion) em Parquet.
- [x] Containerização da aplicação para ambiente isolado.
- [x] Deploy do dashboard visual no Streamlit Cloud.
- [x] Integração de Reverse ETL para Google Drive (In-Place Update).
- [ ] Implementação de Orquestração via GitHub Actions (Cron).
- [ ] Migração de storage para Object Storage (AWS S3 ou GCP).
- [ ] Meta: Classificar 25% da base total até o fim do mês.
