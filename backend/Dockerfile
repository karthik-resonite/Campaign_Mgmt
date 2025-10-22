FROM python:3.10

WORKDIR /code

# Copy requirements first
COPY requirement.txt /code/requirement.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirement.txt

# Copy app source
COPY app /code/app

# Copy SSL certs into the image
COPY redsocks.mu.key /code/redsocks.mu.key
COPY redsocks_mu.pem /code/redsocks_mu.pem

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--ssl-keyfile=/code/redsocks.mu.key", "--ssl-certfile=/code/redsocks_mu.pem"]
