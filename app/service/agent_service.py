import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from app.service.vector_service import VectorService
from app.service.time_service import TimeService

load_dotenv()

class AgentService:
    def __init__(self, vector_service: VectorService, time_service: TimeService):
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError("UPSTAGE_API_KEY environment variable is required")

        # Upstage API Client 설정
        self.client = OpenAI(api_key=api_key, base_url="https://api.upstage.ai/v1")
        self.vector_service = vector_service
        self.time_service = time_service
        self.model_name = "solar-1-mini-chat"

        # [Function Calling] LLM이 사용할 도구 정의
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current real-time for a specific timezone. Use this when user asks for 'now', 'current time'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "The IANA timezone ID, e.g., 'Asia/Seoul', 'America/New_York', 'Europe/London'.",
                            }
                        },
                        "required": ["timezone"],
                    },
                },
            }
        ]

    def process_query(self, query: str, context_limit: int = 3) -> Dict[str, Any]:
        # Step 1: Retrieve relevant documents using vector search
        search_results = self.vector_service.search(query, n_results=context_limit)

        # Step 2: Prepare context from retrieved documents
        context = self._prepare_context(search_results)

        # Step 3: Generate response using Upstage Solar LLM
        response = self._generate_response(query, context)

        return {
            "query": query,
            "response": response,
            "retrieved_documents": search_results["documents"],
            "document_distances": search_results["distances"],
            "context_used": context
        }

    def _prepare_context(self, search_results: Dict[str, Any]) -> str:
        """
        [수정됨] rules.json 구조에 맞춰 검색 결과를 가독성 있는 문자열로 변환합니다.
        """
        documents = search_results.get("documents", [])
        metadatas = search_results.get("metadatas", [])

        if not documents:
            return "No relevant internal regulations found."

        context_parts = []
        for i, doc in enumerate(documents):
            # 메타데이터 추출 (DB에 저장될 때 office_name 등이 메타데이터로 들어갔다고 가정)
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}

            # rules.json의 특성을 반영한 포맷팅
            office_name = meta.get("office_name", "Unknown Office")
            timezone = meta.get("timezone", "Unknown Timezone")
            country = meta.get("country", "")

            # 문맥 조립
            context_part = (
                f"[Source {i + 1}: {office_name} ({country})]\n"
                f"Timezone: {timezone}\n"
                f"Rule Description: {doc}\n"
            )
            context_parts.append(context_part)

        return "\n".join(context_parts)

    def _generate_response(self, query: str, context: str) -> str:
        # rules.json 데이터를 기반으로 한 System Prompt 강화
        system_prompt = (
            "You are a smart AI assistant for a global company. "
            "Use the provided Context to answer questions. "
            "IMPORTANT: If the user asks about availability, office hours, or contact (e.g., 'Can I call?'), "
            "you MUST use the 'get_current_time' tool to get the real-time of that specific timezone. "
            "Do not guess the time. Check it using the tool."
        )

        user_prompt = f"""Context:
{context}

Question: {query}

Please provide a helpful response based on the context above."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model="solar-1-mini-chat",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=500
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # [디버깅] 실제 도구 호출이 잡혔는지 서버 로그로 확인
            print(f"🤖 AI Response Content: {response_message.content}")
            print(f"🔧 Tool Calls Detected: {tool_calls}")

            # 2. 도구 실행이 필요한 경우
            if tool_calls:
                # 대화 내역에 "나 도구 쓸게"라는 AI의 메시지를 추가
                messages.append(response_message)

                for tool_call in tool_calls:
                    if tool_call.function.name == "get_current_time":
                        args = json.loads(tool_call.function.arguments)
                        timezone = args.get("timezone")

                        print(f"⏰ Checking time for: {timezone}")

                        # 실제 함수 실행 (TimeService)
                        tool_result = self.time_service.get_current_time(timezone)

                        print(f"tool result: {tool_result}")

                        # 결과 대화 내역에 추가
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "get_current_time",
                            "content": json.dumps(tool_result)  # 반드시 문자열로 변환
                        })

                # 3. 도구 결과를 포함해서 최종 답변 생성
                final_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1
                )

                final_content = final_response.choices[0].message.content

                return final_content if final_content else "죄송합니다. 시간을 확인했으나 답변을 생성하지 못했습니다."

            # 도구를 안 쓴 경우
            content = response_message.content
            return content if content else "답변을 생성할 수 없습니다."

        except Exception as e:
            print(f"❌ Error in _generate_response: {e}")
            return f"Error during generation: {str(e)}"


    def add_knowledge(self, documents: List[str], metadatas: List[Dict[str, Any]] = None):
        try:
            self.vector_service.add_documents(documents, metadatas)
            return {"status": "success", "message": f"Added {len(documents)} documents to knowledge base"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to add documents: {str(e)}"}

    def get_knowledge_stats(self):
        return self.vector_service.get_collection_info()