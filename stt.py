import tempfile
import os

from openai import OpenAI


def transcribe(ogg_bytes: bytes, api_key: str) -> str:
    client = OpenAI(api_key=api_key)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(ogg_bytes)
        tmp_path = f.name
    try:
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return result.text
    finally:
        os.unlink(tmp_path)
