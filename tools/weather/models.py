from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeatherInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    location: str = Field(min_length=1)

    @field_validator("location")
    @classmethod
    def normalize_location(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("location must not be blank")
        return normalized


class WeatherLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    admin1: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


class CurrentWeather(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: Optional[str] = None
    weather: str
    temperature_c: Optional[float] = None
    apparent_temperature_c: Optional[float] = None
    relative_humidity_percent: Optional[float] = None
    precipitation_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None


class DailyWeather(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    label: str
    weather: str
    temperature_max_c: Optional[float] = None
    temperature_min_c: Optional[float] = None
    precipitation_probability_max_percent: Optional[float] = None
    wind_speed_max_kmh: Optional[float] = None


class WeatherData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: WeatherLocation
    current: CurrentWeather
    daily: list[DailyWeather]
