FROM python:3.11-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libffi-dev \
        libssl-dev \
        libjpeg-dev \
        zlib1g-dev \
        libtiff5-dev \
        libopenjp2-7-dev \
        libfreetype6-dev \
        libwebp-dev \
        liblcms2-dev \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pip setuptools wheel
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
