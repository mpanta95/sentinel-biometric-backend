FROM python:3.11-slim

# Installiamo le dipendenze di sistema minime per OpenCV e dlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# TRUCCO: Diciamo a pip di NON compilare dlib da zero ma di usare i pacchetti precompilati (wheels)
RUN pip install --no-cache-dir cmake wheel setuptools

# Installiamo prima dlib da un binario precompilato per evitare il blocco degli 8GB
RUN pip install --no-cache-dir https://github.com/vstakhov/ai-examples/raw/master/dlib-wheels/dlib-19.24.1-cp311-cp311-linux_x86_64.whl || pip install --no-cache-dir dlib==19.24.2

# Copiamo il resto dei file e installiamo i requisiti rimanenti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server_sicurezza.py"]
