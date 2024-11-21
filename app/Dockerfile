FROM python:3.10-slim
RUN apt-get update && apt-get install -y chromium \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY ./app/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "api.py"]
