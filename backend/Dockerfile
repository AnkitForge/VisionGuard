FROM python:3.10-slim

# Create a non-root user for security (required by some cloud providers like Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Switch back to root temporarily to install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Fix permissions for the app directory
RUN chown -R user:user /app
USER user

# Copy requirements first to leverage Docker cache
COPY --chown=user requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=user . .

# Hugging Face Spaces exposes port 7860 by default
EXPOSE 7860

# Ensure the database and storage directories exist with correct permissions
RUN mkdir -p storage
RUN mkdir -p instance

# Start the application using Gunicorn binding to port 7860
# Timeout is set to 120s to allow heavy ML models to load into memory
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "4", "--timeout", "120", "run:app"]
