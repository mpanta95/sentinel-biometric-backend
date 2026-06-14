FROM python:3.11

WORKDIR /app

# Installiamo cmake e wheel necessari per i pacchetti biometrici
RUN pip install --no-cache-dir cmake wheel setuptools

# Scarichiamo dlib già pronto ed evitiamo la compilazione pesante
RUN pip install --no-cache-dir https://github.com/vstakhov/ai-examples/raw/master/dlib-wheels/dlib-19.24.1-cp311-cp311-linux_x86_64.whl || pip install --no-cache-dir dlib==19.24.2

# Copiamo i requisiti e installiamo il resto delle librerie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server_sicurezza.py"]
