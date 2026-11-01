FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir vosk==0.3.45

WORKDIR /app
COPY vosk_stt_server.py /app/vosk_stt_server.py

ENV VOSK_MODEL_DIR=/models/vosk-model-cn
ENV PORT=9001
EXPOSE 9001

CMD ["python", "-u", "/app/vosk_stt_server.py"]
