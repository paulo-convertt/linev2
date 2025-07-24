FROM python:3.12-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Instalar uv
RUN pip install uv

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de configuração do Python
COPY pyproject.toml uv.lock ./

# Instalar dependências usando uv e gunicorn
RUN uv sync --frozen && uv add gunicorn

# Copiar código fonte e arquivos de configuração
COPY src/ ./src/
COPY gunicorn.conf.py ./
COPY start.sh ./

# Tornar o script executável
RUN chmod +x start.sh

# Expor porta
EXPOSE 8000

# Comando para executar a aplicação
CMD ["./start.sh"]
