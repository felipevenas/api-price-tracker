FROM python:3.10-slim

WORKDIR /code

# Evita gerar arquivos pyc e faz o output ser imediato nos logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependências de compilação básicas para libs Python (como bcrypt) se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /code/
