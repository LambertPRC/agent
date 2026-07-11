import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI

from tools.weather import getWeather

from .prompt_template import prompt


load_dotenv()

apikey = os.getenv("OPENAI_KEY")
base_url = os.getenv("BASE_URL")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=apikey,
    openai_api_base=base_url,
)

agent = create_tool_calling_agent(
    llm=llm,
    tools=[getWeather],
    prompt=prompt,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[getWeather],
    verbose=False,
    handle_parsing_errors=(
        "模型返回了无法解析的工具调用，请根据工具参数定义重新生成。"
    ),
    max_iterations=5,
    max_execution_time=60,
)


def _prepare_agent_input(
    messages: list[dict[str, str]],
) -> tuple[str, list[BaseMessage]]:
    if not isinstance(messages, list):
        raise TypeError("messages must be a list")

    current_user_index = None
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        if message.get("role") == "user":
            current_user_index = index
        elif message.get("role") == "assistant":
            current_user_index = None

    if current_user_index is None:
        raise ValueError("messages must end with a non-empty user message")

    current_input = messages[current_user_index]["content"].strip()
    chat_history: list[BaseMessage] = []
    for message in messages[:current_user_index]:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        if role == "user":
            chat_history.append(HumanMessage(content=content))
        elif role == "assistant":
            chat_history.append(AIMessage(content=content))

    return current_input, chat_history


def agent_invoke(messages: list[dict[str, str]]) -> dict[str, Any]:
    current_input, chat_history = _prepare_agent_input(messages)
    response = agent_executor.invoke(
        {
            "input": current_input,
            "chat_history": chat_history,
        }
    )
    print(response["output"])
    return response
