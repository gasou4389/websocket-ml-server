# Use Python as the base image
FROM python:3.10

# Install required system dependencies
RUN apt-get update && apt-get install -y caddy

# Set the working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy Caddyfile for automatic HTTPS setup
COPY Caddyfile /etc/caddy/Caddyfile

# Expose necessary ports
EXPOSE 443

# Run Caddy as the primary process
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]

