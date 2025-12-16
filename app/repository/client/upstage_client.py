import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models.schemas.chat import ChatRequest

load_dotenv()

class UpstageClient:
    def __init__(self):
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY environment variable is required")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1"
        )

    def chat_streaming(self, message: ChatRequest):
        response = self.client.chat.completions.create(
            model="solar-pro2",
            messages=[
                {
                    "role": "user",
                    "content": message.prompt
                }
            ],
            stream=False,
        )
        return response.choices[0].message


