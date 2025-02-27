# Escolha a imagem base com Python 3.10
FROM python:3.10-slim

# Instala o ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Diretório de trabalho
WORKDIR /app

# Copia o requirements.txt para o container
COPY requirements.txt /app

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código para o container
COPY . /app

# Exponha a porta (boa prática)
EXPOSE 8000

# Comando para rodar seu app (usa a variável $PORT com fallback para 8000)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
