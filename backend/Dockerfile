# Dockerfile
# Imagem base Python slim (menor tamanho)
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /code

# Copia e instala as dependências primeiro (cache de layers Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Expõe a porta da API
EXPOSE 8000

# Comando para iniciar a aplicação em produção
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
