from typing import Any

import httpx

from tools.common import ToolExecutionError, standard_tool

from .models import WeatherData, WeatherInput


GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 10.0
TOOL_META = {
    "provider": "Open-Meteo",
    "source_url": "https://open-meteo.com/",
}

WEATHER_CODE_TEXT = {
    0: "晴",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中等毛毛雨",
    55: "强毛毛雨",
    56: "轻度冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "轻度冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "米雪",
    80: "小阵雨",
    81: "中等阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴伴轻度冰雹",
    99: "雷暴伴强冰雹",
}


def _weather_text(code: Any) -> str:
    try:
        normalized_code = int(code)
    except (TypeError, ValueError):
        return "未知"
    return WEATHER_CODE_TEXT.get(normalized_code, f"未知天气代码 {normalized_code}")


def _value_at(values: Any, index: int) -> Any:
    if isinstance(values, list) and index < len(values):
        return values[index]
    return None


def _build_daily_forecast(daily: Any) -> list[dict[str, Any]]:
    if not isinstance(daily, dict):
        return []

    dates = daily.get("time")
    if not isinstance(dates, list):
        return []

    forecasts = []
    for index, date in enumerate(dates[:7]):
        weather_code = _value_at(daily.get("weather_code"), index)
        forecasts.append(
            {
                "date": date,
                "label": "今天" if index == 0 else "明天" if index == 1 else date,
                "weather": _weather_text(weather_code),
                "temperature_max_c": _value_at(
                    daily.get("temperature_2m_max"), index
                ),
                "temperature_min_c": _value_at(
                    daily.get("temperature_2m_min"), index
                ),
                "precipitation_probability_max_percent": _value_at(
                    daily.get("precipitation_probability_max"), index
                ),
                "wind_speed_max_kmh": _value_at(
                    daily.get("wind_speed_10m_max"), index
                ),
            }
        )
    return forecasts


def _invalid_response() -> ToolExecutionError:
    return ToolExecutionError(
        "INVALID_RESPONSE",
        "Open-Meteo 返回了无法解析的数据",
        retryable=False,
    )


@standard_tool(
    description="根据城市名称查询当前天气和未来七天天气预报",
    meta=TOOL_META,
    args_schema=WeatherInput,
    data_model=WeatherData,
)
def getWeather(location: str) -> dict[str, Any]:
    """Query Open-Meteo and return weather business data."""
    if not isinstance(location, str) or not location.strip():
        raise ToolExecutionError(
            "INVALID_LOCATION",
            "城市名称不能为空",
            retryable=False,
        )
    location = location.strip()

    try:
        geocoding_response = httpx.get(
            GEOCODING_API_URL,
            params={
                "name": location,
                "count": 1,
                "language": "zh",
                "format": "json",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        geocoding_response.raise_for_status()
        geocoding_data = geocoding_response.json()
        if not isinstance(geocoding_data, dict):
            raise _invalid_response()

        places = geocoding_data.get("results") or []
        if not isinstance(places, list):
            raise _invalid_response()
        if not places:
            raise ToolExecutionError(
                "LOCATION_NOT_FOUND",
                f"未找到地点：{location}",
                retryable=False,
            )

        place = places[0]
        if not isinstance(place, dict):
            raise _invalid_response()

        forecast_response = httpx.get(
            FORECAST_API_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,apparent_temperature,relative_humidity_2m,"
                    "precipitation,weather_code,wind_speed_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,wind_speed_10m_max"
                ),
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm",
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        forecast_response.raise_for_status()
        weather_data = forecast_response.json()
        if not isinstance(weather_data, dict):
            raise _invalid_response()
    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code
        raise ToolExecutionError(
            "HTTP_ERROR",
            f"Open-Meteo 请求失败，HTTP 状态码：{status_code}",
            retryable=status_code == 429 or status_code >= 500,
            meta={"status_code": status_code},
        ) from error
    except httpx.RequestError as error:
        raise ToolExecutionError(
            "NETWORK_ERROR",
            "Open-Meteo 请求失败，请检查网络连接后重试",
            retryable=True,
        ) from error
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise _invalid_response() from error

    current = weather_data.get("current")
    if not isinstance(current, dict):
        current = {}

    return {
        "location": {
            "name": place.get("name"),
            "admin1": place.get("admin1"),
            "country": place.get("country"),
            "latitude": place.get("latitude"),
            "longitude": place.get("longitude"),
            "timezone": weather_data.get("timezone"),
        },
        "current": {
            "time": current.get("time"),
            "weather": _weather_text(current.get("weather_code")),
            "temperature_c": current.get("temperature_2m"),
            "apparent_temperature_c": current.get("apparent_temperature"),
            "relative_humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
        },
        "daily": _build_daily_forecast(weather_data.get("daily")),
    }
