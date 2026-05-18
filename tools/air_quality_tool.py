def get_air_quality(latitude: float, longitude: float) -> dict:
    """
    Fake air quality data for MVP.

    Later this can be replaced by:
    - Taiwan EPA air quality open data
    """
    return {
        "aqi": 68,
        "level": "普通",
        "pm25": "18 μg/m³",
        "summary": "空氣品質普通，對一般族群影響不大，但敏感族群仍需注意。"
    }