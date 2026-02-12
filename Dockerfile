FROM python:3.9

WORKDIR /app

# Create directory structure for persistent volumes
RUN mkdir -p /datasets /ml/models && \
    chmod -R 777 /datasets /ml/models

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
