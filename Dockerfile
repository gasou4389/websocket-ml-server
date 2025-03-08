# Use an official Python runtime as a parent image
FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y certbot nginx

# Set the working directory
WORKDIR /app

# Copy your project files
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Generate SSL certificates using Certbot (Replace YOUR_DOMAIN)
RUN certbot certonly --standalone --non-interactive --agree-tos --email Brandon.Moyer8884@outlook.com -d websocket-ml-server-production.up.railway.app

# Expose port 8080
EXPOSE 8080

# Start the WebSocket server with SSL
CMD ["uvicorn", "websocket_ml_server:app", "--host", "0.0.0.0", "--port", "8080", "--ssl-keyfile", "/etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem", "--ssl-certfile", "/etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem"]
