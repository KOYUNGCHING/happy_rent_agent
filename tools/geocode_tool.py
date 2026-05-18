import requests


def geocode_location(location_name: str) -> dict:
    """
    Convert a location name into latitude, longitude, city, and district
    using OpenStreetMap Nominatim API.

    Example:
        Input: "台北車站"
        Output:
        {
            "location_name": "台北車站",
            "latitude": 25.0477,
            "longitude": 121.5170,
            "city": "臺北市",
            "district": "中正區",
            "display_name": "臺北車站, ..."
        }
    """

    query = location_name.strip()

    if not query:
        raise ValueError("Location name cannot be empty.")

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "accept-language": "zh-TW"
    }

    headers = {
        "User-Agent": "happy-rent-agent/1.0 (student project)"
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    results = response.json()

    if not results:
        raise ValueError(f"找不到地點：{location_name}")

    first_result = results[0]

    address = first_result.get("address", {})

    city = (
        address.get("city")
        or address.get("county")
        or address.get("state")
        or "未知城市"
    )

    district = (
        address.get("city_district")
        or address.get("suburb")
        or address.get("town")
        or address.get("village")
        or "未知行政區"
    )

    return {
        "location_name": location_name,
        "latitude": float(first_result["lat"]),
        "longitude": float(first_result["lon"]),
        "city": city,
        "district": district,
        "display_name": first_result.get("display_name", "")
    }