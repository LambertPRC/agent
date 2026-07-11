import os

from langchain.agents import create_react_agent,AgentExecutor
from tools.weather import getWeather
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from .prompt_template import prompt


load_dotenv()

apikey = os.getenv("OPENAI_KEY")
base_url = os.getenv("BASE_URL")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=apikey,
    openai_api_base=base_url,
)


agent = create_react_agent(
    llm=llm,
    tools=[getWeather],
    prompt=prompt
)


# 用 AgentExecutor 包装（关键！）
agent_executor = AgentExecutor(
    agent=agent,
    tools=[getWeather],
    verbose=True  # 可选，打印推理过程
)

def agent_invoke(messages: list):
    print(1)
    user_input = "\n".join(
        message.get("content", "")
        for message in messages
        if message.get("role") == "user" and message.get("content")
    )
    if not user_input:
        raise ValueError("messages must contain at least one non-empty user message")

    rsp = agent_executor.invoke({
        "input": user_input
    })
    print(rsp)
