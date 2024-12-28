#!/bin/sh

# Log the start of the script
echo "Starting entrypoint script..."

# Activate the virtual environment
echo "Activating virtual environment..."
. /app/venv/bin/activate

# Log the activation of the virtual environment
echo "Virtual environment activated. Starting Flask application..."

# Run the Flask application
python /app/run.py

# Log the completion of the script
echo "Entrypoint script completed."
