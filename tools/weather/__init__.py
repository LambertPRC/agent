from langchain.tools import tool


@tool(description="获取指定城市的天气信息")
def getWeather(location: str) -> str:
    return f"Current weather in {location} is sunny"