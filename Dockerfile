FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcb1 libx11-6 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libasound2 \
    fonts-liberation libgtk-3-0 curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app /app
COPY app/requirements.txt /app/requirements.txt
COPY app/startup.sh /app/startup.sh
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /app/startup.sh && /app/startup.sh
ENV PORT=8000
EXPOSE 8000
CMD ["python","app.py"]
