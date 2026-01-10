import json
from pydoc import describe

from openai import OpenAI

from app.service.time_service import TimeService


def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if unit is None:
        unit = "fahrenheit"

    if "seoul" in location.lower():
        return json.dumps({"location": "Seoul", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps(
            {"location": "San Francisco", "temperature": "72", "unit": unit}
        )
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})



# Step 2: Send the query and available functions to the model
def run_conversation(client: OpenAI, time_service: TimeService, prompt):
    messages = [
        {
            "role": "user",
            # "content": "What's the weather like in San Francisco, Seoul, and Paris?",
            "content": prompt,
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Retrieves current time for the given timezone.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "The IANA timezone identifier to get the current time for.",
                            "enum": [
                                "Asia/Seoul",
                                "Asia/Tokyo",
                                "Asia/Shanghai",
                                "Asia/Singapore",
                                "Asia/Dubai",
                                "Europe/London",
                                "Europe/Paris",
                                "Europe/Berlin",
                                "Europe/Moscow",
                                "America/New_York",
                                "America/Chicago",
                                "America/Vancouver",
                                "America/Sao_Paulo",
                                "Australia/Sydney",
                                "Pacific/Auckland",
                                "Asia/Kolkata",
                                "Asia/Bangkok",
                                "Africa/Johannesburg",
                                "Pacific/Honolulu"
                            ]
                        }
                    },
                    "required": ["timezone"],
                },
            },
        }
    ]

    # Step 3: Check if the model has requested a function call
    # The model identifies that the query requires external data (e.g., real-time weather) and decides to call a relevant function, such as a weather API.
    response = client.chat.completions.create(
        model="solar-pro2",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    print(f"🤖 [DEBUG] Tool Calls 결과: {tool_calls}")

    # Step 4: Execute the function call
    # The JSON response from the model may not always be valid, so handle errors appropriately
    if tool_calls:
        available_functions = {
            "get_current_time": time_service.get_current_time,
        }  # You can define multiple functions here as needed
        messages.append(response_message)  # Add the assistant's reply to the conversation history

        # Step 5: Process each function call and provide the results to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)

            print(f"🚀 [DEBUG] 함수 실행 시작: {function_name}")

            function_response = function_to_call(
                timezone=function_args.get("timezone")
            )  # Call the function with the provided arguments

            # TimeService에서 리턴받은 값이 여기로 잘 넘어왔는지 확인합니다.
            print(f"💎 [DEBUG] tools.py가 받은 리턴값: {function_response}")

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # Append the function response to the conversation history

        # Step 6: Generate a new response from the model using the updated conversation history
        second_response = client.chat.completions.create(
            model="solar-pro2",
            messages=messages,
        )

        final_answer = second_response.choices[0].message.content

        # [✅ 눈으로 확인하기] 최종적으로 AI가 뭐라고 답변했는지 콘솔에 출력!
        print("--------------------------------------------------")
        print(f"🏁 [FINAL ANSWER] AI의 최종 답변:\n{final_answer}")
        print("--------------------------------------------------")
        return second_response  # Return the final response from the model
    return response_message
