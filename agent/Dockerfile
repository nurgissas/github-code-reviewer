FROM python:3.9-slim

WORKDIR /app

# install system dependencies
# libpq-dev is needed for psycopg2 - postgresql driver
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# copy requirements and install python packages
COPY agent/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY agent .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]