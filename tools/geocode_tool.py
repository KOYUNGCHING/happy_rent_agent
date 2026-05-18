def geocode_location(location_name: str) -> dict:
    """
    Fake geocoding function for MVP.

    Later this can be replaced by:
    - OpenStreetMap / Nominatim
    - Google Geocoding API
    - Taiwan government geospatial data
    """
    return {
        "location_name": location_name,
        "latitude": 25.0478,
        "longitude": 121.5170,
        "city": "台北市",
        "district": "中正區"
    }