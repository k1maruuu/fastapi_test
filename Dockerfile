FROM python:3.13.2-slim

WORKDIR /app

# Копируем requirements.txt для установки зависимостей
COPY requirements.txt .

# Устанавливаем зависимости с очисткой кэша
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /tmp/* /root/.cache/pip

# Копируем остальной код приложения
COPY . .

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Запускаем приложение с uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# БЕЗ --reload в продакшене

