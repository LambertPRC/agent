import os
from openai import OpenAI
import httpx
from dotenv import load_dotenv
from pathlib import Path

# --- 核心修改：精确指定 .env 文件路径 ---
# 1. 获取当前文件 (比如 openai_client.py) 的绝对路径
current_file_path = Path(__file__).resolve()
# 2. 获取当前文件所在的目录 (比如 .../infra/openai_client)
current_dir = current_file_path.parent
# 3. 向上回退两级，找到项目根目录 (比如 .../agent)
#    如果你的 .env 在 infra 目录下，就只写 .parent
project_root = current_dir.parent.parent
# 4. 拼接出 .env 文件的完整路径
env_path = project_root / '.env'

# 5. 加载指定路径的 .env 文件
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_KEY")
base_url = os.getenv("BASE_URL")


OpenAI_Client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    # http_client = httpx.Client(proxy="http://127.0.0.1:7897")
)


def SendMessage(messages: list, model="deepseek-chat"):
    response = OpenAI_Client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,

    )
    return response.choices[0].message.content