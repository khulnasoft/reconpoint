FROM ubuntu:20.04

# Install necessary tools and dependencies
RUN apt-get update && apt-get install -y \
    postgresql redis nginx python3-pip supervisor \
    bash curl

# Install Python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# Copy application code
COPY ./web /app
WORKDIR /app

# Load environment variables from .env file (devcontainer setup)
COPY ./.env /app/.env
RUN export $(cat /app/.env | xargs) \
    && echo "Environment variables loaded."

# Copy configuration files for supervisor
COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose necessary ports
EXPOSE 5432 6379 8000 8082 443 11434

# Entrypoint to launch supervisor
CMD ["/usr/bin/supervisord"]
