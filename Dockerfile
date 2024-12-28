# Use the official Python image with version 3.10 as the base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script and requirements (if any) to the container
COPY . .

# Create and activate a virtual environment
RUN python -m venv venv

# Activate the virtual environment and install dependencies
RUN . /app/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && pip list

# Add an entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose both the HTTP server port and Flask API port
EXPOSE 8080

# Use the entrypoint script to start the application
ENTRYPOINT ["/app/entrypoint.sh"]
