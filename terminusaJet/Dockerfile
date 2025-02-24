FROM python:3.11

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "eventlet", "--bind", "0.0.0.0:5000", "wsgi:app"]

