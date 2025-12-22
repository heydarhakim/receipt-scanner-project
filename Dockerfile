# 1. Use Python 3.10 Slim (Small & Secure)
FROM python:3.10-slim

# 2. Install system dependencies required by OpenCV (Updated for Debian Bookworm)
# CHANGED: 'libgl1-mesa-glx' -> 'libgl1'
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install CPU-only PyTorch & Torchvision
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 5. Copy requirements and install the rest
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . .

# 7. Create necessary folders for SQLite and Uploads
RUN mkdir -p instance static/uploads

# 8. Define the Environment Variable for Flask
ENV FLASK_APP=run.py

# 9. The command to run the app
# Use 1 worker to save RAM, 8 threads for concurrency, and 120s timeout for slow OCR
CMD sh -c "gunicorn run:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120"