from openai import OpenAI


def synthesize(text: str, api_key: str) -> bytes:
    client = OpenAI(api_key=api_key)
    response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
    return response.content
