FROM python:3.12-slim

# avoid python buffering logs
ENV PYTHONUNBUFFERED=1

# create dir
WORKDIR /app

# install sys dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
