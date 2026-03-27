FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/services/bff

RUN addgroup --system app && adduser --system --ingroup app app

COPY services/bff/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY services/bff/app app

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
