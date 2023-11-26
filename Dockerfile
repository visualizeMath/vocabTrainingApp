FROM python:3.8

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/
# Add a dummy file or change the timestamp to invalidate the cache
RUN touch /app/dummy.txt

CMD ["python", "app.py"]
