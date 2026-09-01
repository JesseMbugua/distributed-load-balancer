FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir flask requests

COPY consistent_hash.py app.py ./

EXPOSE 5000
CMD ["python", "app.py"]