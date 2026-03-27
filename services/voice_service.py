import httpx
import logging
from config import WHISPER_API_URL


async def transcribe_voice(file_content: bytes, filename: str) -> str| None:
    """
    Отправляет байты аудиофайла на Whisper API и возвращает текст.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        files = {'file': (filename, file_content, 'audio/ogg')}
        try:
            response = await client.post(WHISPER_API_URL, files=files) #type:ignore
            response.raise_for_status()
            data = response.json()
            return data.get("text", "Не удалось распознать текст.")
        except Exception as e:
            logging.error(f"Error calling Whisper API: {e}")
            return None