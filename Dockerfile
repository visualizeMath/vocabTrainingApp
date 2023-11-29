FROM python:3.8

WORKDIR /app

COPY src/main/webapp/ .

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 5000
COPY . /app/

CMD ["python", "app.py"]
