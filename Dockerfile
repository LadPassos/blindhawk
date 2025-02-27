RUN apt-get update && apt-get install -y ffmpeg
# Escolha a imagem base com Python 3.10
FROM python:3.10-slim

# Diretório de trabalho
WORKDIR /app

# Copia o requirements.txt
COPY requirements.txt /app

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código para o container
COPY . /app

# Exponha a porta (não estritamente necessário no Render, mas uma boa prática)
EXPOSE 8000

RUN apt-get update && apt-get install -y ffmpeg


# Comando para rodar seu app: adaptado para usar a var $PORT com fallback para 8000
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
