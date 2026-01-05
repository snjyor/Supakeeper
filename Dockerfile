FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ ./src/
COPY main.py .
COPY pyproject.toml .

# Create logs directory
RUN mkdir -p logs

# Default command (can be overridden)
CMD ["python", "main.py", "--daemon"]

