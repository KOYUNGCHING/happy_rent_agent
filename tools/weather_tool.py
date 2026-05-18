def get_weather(latitude: float, longitude: float) -> dict:
    """
    Fake weather data for MVP.

    Later this can be replaced by:
    - Central Weather Administration API
    - OpenWeatherMap API
    """
    return {
        "temperature": "31°C",
        "weather": "多雲",
        "rain_probability": "20%",
        "summary": "今日天氣偏熱，降雨機率低，外出看房影響不大。"
    }