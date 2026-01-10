import os
import json
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

from app.core.tools import run_conversation
from app.models.schemas.user import ChatRequest
from app.service.time_service import TimeService

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
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1"
        )

    def chat_streaming(self, message: ChatRequest):
        stream = self.client.chat.completions.create(
            model="solar-pro2",
            messages=message.prompt,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    async def chat_streaming_async(self, message: ChatRequest):
        stream = await self.async_client.chat.completions.create(
            model="solar-pro2",
            messages=message.prompt,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def chat_with_tools(self, time_service: TimeService, prompt):
        """간단한 tool calling (강의용)"""
        return run_conversation(self.client, time_service, prompt)

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model="solar-embedding-1-large-query",
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise RuntimeError(f"Failed to create embeddings: {str(e)}")

    def create_embedding(self, text: str) -> List[float]:
        return self.create_embeddings([text])[0]