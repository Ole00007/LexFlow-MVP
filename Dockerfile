FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port Railway provides
EXPOSE 5000

# Railway will use startCommand from railway.toml; this is the fallback
CMD gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 2 wsgi:app