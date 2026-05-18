def get_facilities(latitude: float, longitude: float) -> dict:
    """
    Fake facility data for MVP.

    Later this can be replaced by:
    - Google Places API
    - OpenStreetMap Overpass API
    - Taiwan open data
    """
    return {
        "convenience_stores": 15,
        "restaurants": 80,
        "clinics": 10,
        "parks": 2,
        "facility_score": 90,
        "summary": "生活機能完整，外食、採買與醫療資源都很方便。"
    }