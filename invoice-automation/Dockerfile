FROM python:3.11-slim

WORKDIR /usr/src/app

RUN pip install --no-cache-dir pip setuptools wheel

COPY ./app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
