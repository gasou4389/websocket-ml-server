# Use Python base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the correct port (Use ENV variable)
EXPOSE 8080

# Start WebSocket server, dynamically setting the port
CMD ["sh", "-c", "uvicorn websocket_ml_server:app --host 0.0.0.0 --port ${PORT:-8080}"]


