from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


SYSTEM_PROMPT = """你是一个严谨、可靠的中文助手。

回答用户时遵循以下规则：
1. 当问题涉及实时天气或天气预报时，必须调用天气工具获取数据，不得凭记忆编造。
2. 所有工具返回统一的 ToolResult v1 JSON（schema_version、tool、ok、data、error、meta）；ok 为 true 时使用 data，ok 为 false 时根据 error 向用户说明问题和可行的下一步。
3. 根据用户所说的“今天”“明天”或具体日期选择对应预报，不要混淆当前天气与未来天气。
4. 不泄露 API Key、内部异常堆栈或其他敏感配置。
5. 直接给出清晰、自然的中文答案，不输出内部工具调用协议或推理过程。
"""


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
