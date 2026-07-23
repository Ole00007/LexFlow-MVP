FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port Railway provides
EXPOSE 5000

# Start with python wsgi.py (wsgi.py imports app from app.py)
CMD ["python", "wsgi.py"]