#!/bin/bash
set -e

INSTANCE=cerebro-bot
ZONE=us-central1-a
PROJECT=cerebro-489100
REMOTE=/home/AndrewCamp/cerebro

echo "==> Copying files..."
gcloud compute scp --recurse \
  bot.py config.py handler.py stt.py tts.py requirements.txt \
  db/ llm/ memory/ \
  ${INSTANCE}:${REMOTE} \
  --zone ${ZONE} --project ${PROJECT}

echo "==> Installing any new dependencies..."
gcloud compute ssh ${INSTANCE} --zone ${ZONE} --project ${PROJECT} \
  --command "cd ${REMOTE} && venv/bin/pip install --quiet -r requirements.txt"

echo "==> Restarting service..."
gcloud compute ssh ${INSTANCE} --zone ${ZONE} --project ${PROJECT} \
  --command "sudo systemctl restart cerebro"

echo "==> Tailing logs (Ctrl+C to exit)..."
gcloud compute ssh ${INSTANCE} --zone ${ZONE} --project ${PROJECT} \
  --command "sudo journalctl -u cerebro -f --no-pager"
