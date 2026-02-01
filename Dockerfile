FROM python:3.10-slim

WORKDIR /app

# Copy the service directory
COPY jimeng-dify-service/ ./jimeng-dify-service/

# Install dependencies
RUN pip install --no-cache-dir -r jimeng-dify-service/requirements.txt

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
# Ensure the module can be found
ENV PYTHONPATH=/app/jimeng-dify-service

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "jimeng-dify-service/app.py"]
