#!/bin/sh

# Запускаем uvicorn в фоновом режиме
python3 asgi.py &

# Запускаем main.py
python3 main.py
