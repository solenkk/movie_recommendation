FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG False

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "movie_app.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]