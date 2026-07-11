import json
import unittest
from unittest.mock import patch

import httpx

import tools.weather as weather


class WeatherToolTests(unittest.TestCase):
    def _response(self, url, payload, status_code=200):
        return httpx.Response(
            status_code,
            json=payload,
            request=httpx.Request("GET", url),
        )

    def test_success_uses_tool_result_and_typed_weather_data(self):
        geocoding = self._response(
            weather.GEOCODING_API_URL,
            {
                "results": [
                    {
                        "name": "杭州",
                        "admin1": "浙江",
                        "country": "中国",
                        "latitude": 30.25,
                        "longitude": 120.17,
                    }
                ]
            },
        )
        forecast = self._response(
            weather.FORECAST_API_URL,
            {
                "timezone": "Asia/Shanghai",
                "current": {
                    "time": "2026-07-11T12:00",
                    "temperature_2m": 31.2,
                    "apparent_temperature": 35.0,
                    "relative_humidity_2m": 70,
                    "precipitation": 0.0,
                    "weather_code": 2,
                    "wind_speed_10m": 8.5,
                },
                "daily": {
                    "time": ["2026-07-11", "2026-07-12"],
                    "weather_code": [2, 61],
                    "temperature_2m_max": [34.0, 32.0],
                    "temperature_2m_min": [27.0, 26.0],
                    "precipitation_probability_max": [20, 70],
                    "wind_speed_10m_max": [15.0, 18.0],
                },
            },
        )

        with patch.object(weather.httpx, "get", side_effect=[geocoding, forecast]):
            result = json.loads(weather.getWeather.invoke({"location": " 杭州 "}))

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool"], "getWeather")
        self.assertEqual(result["data"]["location"]["name"], "杭州")
        self.assertEqual(result["data"]["daily"][1]["label"], "明天")
        self.assertEqual(result["meta"]["provider"], "Open-Meteo")

    def test_location_not_found_is_a_business_error(self):
        response = self._response(weather.GEOCODING_API_URL, {"results": []})

        with patch.object(weather.httpx, "get", return_value=response) as mocked_get:
            result = json.loads(weather.getWeather.invoke("不存在的地方"))

        self.assertEqual(mocked_get.call_count, 1)
        self.assertEqual(result["error"]["code"], "LOCATION_NOT_FOUND")
        self.assertFalse(result["error"]["retryable"])

    def test_retryable_http_error_is_standardized(self):
        response = self._response(
            weather.GEOCODING_API_URL,
            {"error": True},
            status_code=503,
        )

        with patch.object(weather.httpx, "get", return_value=response):
            result = json.loads(weather.getWeather.invoke("杭州"))

        self.assertEqual(result["error"]["code"], "HTTP_ERROR")
        self.assertTrue(result["error"]["retryable"])
        self.assertEqual(result["meta"]["status_code"], 503)

    def test_invalid_arguments_are_rejected_before_http(self):
        with patch.object(weather.httpx, "get") as mocked_get:
            wrong_type = json.loads(weather.getWeather.invoke({"location": 123}))
            extra_field = json.loads(
                weather.getWeather.invoke({"location": "杭州", "extra": "x"})
            )

        self.assertEqual(mocked_get.call_count, 0)
        self.assertEqual(wrong_type["error"]["code"], "INVALID_ARGUMENTS")
        self.assertEqual(extra_field["error"]["code"], "INVALID_ARGUMENTS")


if __name__ == "__main__":
    unittest.main()
