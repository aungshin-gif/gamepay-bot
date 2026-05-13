FROM python:3.11-slim

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the filename matches your actual file
# GitHub ထဲမှာ app(4).py ကို app.py လို့ နာမည်ပြောင်းထားပေးပါ
CMD ["python", "app.py"]

