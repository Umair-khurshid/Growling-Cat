# Stage 1: Builder
FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies and clean up apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Image
FROM python:3.9-slim

# Create a non-root user
RUN useradd --create-home appuser

WORKDIR /home/appuser/app

# Copy virtual environment and application code
COPY --from=builder /opt/venv /opt/venv
COPY . .

# Make sure the app user owns the files
RUN chown -R appuser:appuser /home/appuser/app

USER appuser

# Set the path to the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Expose the Streamlit port
EXPOSE 8501

# Set the command to run the app
CMD ["/opt/venv/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
