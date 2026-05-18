def get_transport_info(latitude: float, longitude: float) -> dict:
    """
    Fake transport data for MVP.

    Later this can be replaced by:
    - TDX API
    - Google Maps API
    - OpenStreetMap
    """
    return {
        "metro_stations": ["台北車站", "北門站"],
        "bus_stop_count": 12,
        "youbike_station_count": 8,
        "transport_score": 95,
        "summary": "交通非常便利，有捷運、火車、高鐵與多條公車路線。"
    }