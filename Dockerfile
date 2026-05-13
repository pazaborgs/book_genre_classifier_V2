FROM python:3.11-slim

# Variáveis de ambiente para não gerar lixo e não atrasar logs

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y curl build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copia os arquivos de trava de dependência

COPY pyproject.toml uv.lock ./

# Instala as dependências do projeto usando o uv, garantindo que sejam exatamente as versões especificadas no uv.lock

RUN uv sync --frozen --no-dev

# Copia o restante do código da aplicação para o container

COPY . .

# Expõe a porta 8501 para que o Streamlit possa ser acessado externamente

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]