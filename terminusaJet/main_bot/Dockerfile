# Используем базовый образ Python 3.12 slim
FROM python:3.12-slim

# Копируем файл requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем все файлы из текущей директории в контейнер
COPY . .

# Делаем скрипт start.sh исполняемым
RUN chmod +x start.sh

# Команда для запуска скрипта start.sh
CMD ["./start.sh"]