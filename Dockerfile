FROM python:3.14-slim

WORKDIR /My_bot
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "main.py"]