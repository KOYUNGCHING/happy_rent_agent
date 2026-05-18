import requests


def build_overpass_query(latitude: float, longitude: float, radius: int = 800) -> str:
    """
    建立 Overpass API 查詢語法。

    Overpass API 使用自己的查詢語言，叫做 Overpass QL。

    這裡我們查詢指定座標半徑內的幾種生活機能：
    - convenience：便利商店
    - restaurant：餐廳
    - cafe：咖啡廳
    - pharmacy：藥局
    - clinic：診所
    - laundry：自助洗衣 / 洗衣店
    - supermarket：超市
    - bus_stop：公車站

    radius 單位是公尺。
    """

    query = f"""
    [out:json][timeout:25];

    (
      node["shop"="convenience"](around:{radius},{latitude},{longitude});
      node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
      node["amenity"="cafe"](around:{radius},{latitude},{longitude});
      node["amenity"="pharmacy"](around:{radius},{latitude},{longitude});
      node["amenity"="clinic"](around:{radius},{latitude},{longitude});
      node["shop"="laundry"](around:{radius},{latitude},{longitude});
      node["shop"="supermarket"](around:{radius},{latitude},{longitude});
      node["highway"="bus_stop"](around:{radius},{latitude},{longitude});
    );

    out center;
    """

    return query


def classify_osm_element(element: dict) -> str:
    """
    根據 OSM element 的 tags 判斷它是哪一種生活機能。

    OpenStreetMap 的資料會長得像：
    {
        "type": "node",
        "lat": ...,
        "lon": ...,
        "tags": {
            "amenity": "restaurant",
            "name": "..."
        }
    }

    我們要根據 tags 裡的 amenity / shop / highway 來分類。
    """

    tags = element.get("tags", {})

    if tags.get("shop") == "convenience":
        return "convenience_store"

    if tags.get("amenity") == "restaurant":
        return "restaurant"

    if tags.get("amenity") == "cafe":
        return "cafe"

    if tags.get("amenity") == "pharmacy":
        return "pharmacy"

    if tags.get("amenity") == "clinic":
        return "clinic"

    if tags.get("shop") == "laundry":
        return "laundry"

    if tags.get("shop") == "supermarket":
        return "supermarket"

    if tags.get("highway") == "bus_stop":
        return "bus_stop"

    return "other"


def get_element_name(element: dict) -> str:
    """
    取得 OSM 地點名稱。

    有些 OSM 資料沒有 name，
    所以如果沒有名稱，我們就用「未命名地點」代替。
    """

    tags = element.get("tags", {})
    return tags.get("name") or tags.get("name:zh") or "未命名地點"


def summarize_facility_counts(counts: dict) -> str:
    """
    根據生活機能數量產生中文摘要。
    """

    return (
        f"附近約有 {counts['convenience_store']} 間便利商店、"
        f"{counts['restaurant']} 間餐廳、"
        f"{counts['cafe']} 間咖啡廳、"
        f"{counts['pharmacy']} 間藥局、"
        f"{counts['clinic']} 間診所、"
        f"{counts['laundry']} 間洗衣店、"
        f"{counts['supermarket']} 間超市，"
        f"以及 {counts['bus_stop']} 個公車站。"
    )


def calculate_facility_score(counts: dict) -> int:
    """
    根據生活機能數量計算學生生活機能分數。

    這是 MVP 的簡單 scoring rule。

    評分概念：
    - 便利商店、餐廳、公車站對學生很重要
    - 洗衣店、藥局、診所也很重要
    - 咖啡廳、超市是加分項
    """

    score = 0

    # 便利商店，最多加 20 分
    score += min(counts["convenience_store"] * 5, 20)

    # 餐廳，最多加 20 分
    score += min(counts["restaurant"] * 2, 20)

    # 公車站，最多加 15 分
    score += min(counts["bus_stop"] * 3, 15)

    # 洗衣店，最多加 10 分
    score += min(counts["laundry"] * 5, 10)

    # 藥局，最多加 10 分
    score += min(counts["pharmacy"] * 5, 10)

    # 診所，最多加 10 分
    score += min(counts["clinic"] * 5, 10)

    # 超市，最多加 10 分
    score += min(counts["supermarket"] * 5, 10)

    # 咖啡廳，最多加 5 分
    score += min(counts["cafe"] * 2, 5)

    # 分數最高 100
    return min(score, 100)


def get_facilities(latitude: float, longitude: float, radius: int = 800) -> dict:
    """
    使用 OpenStreetMap Overpass API 查詢附近生活機能。

    這個 function 會被 run_agent() 呼叫。

    輸入：
        latitude: 緯度
        longitude: 經度
        radius: 查詢半徑，預設 800 公尺

    輸出：
        dict，包含附近生活機能數量、生活機能分數、摘要與資料來源。
    """

    # Overpass API 有時候某個 endpoint 會暫時不穩，
    # 所以這裡準備多個 endpoint，第一個失敗就換下一個。
    overpass_urls = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]

    # 建立 Overpass QL 查詢字串
    query = build_overpass_query(
        latitude=latitude,
        longitude=longitude,
        radius=radius
    )

    # 準備各類生活機能計數器
    counts = {
        "convenience_store": 0,
        "restaurant": 0,
        "cafe": 0,
        "pharmacy": 0,
        "clinic": 0,
        "laundry": 0,
        "supermarket": 0,
        "bus_stop": 0,
        "other": 0
    }

    nearby_places = []

    # headers 用來告訴 API 我們是誰，以及我們希望拿 JSON
    # 有些公開 API 不喜歡沒有 User-Agent 的 request
    headers = {
        "User-Agent": "happy-rent-agent/1.0 (student project)",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    # 逐一嘗試不同 Overpass endpoint
    for url in overpass_urls:
        try:
            # 這裡改成直接送 query 字串，而不是 data={"data": query}
            # 某些 Overpass server 對 form-data 比較挑，直接送 raw query 較穩。
            response = requests.post(
                url,
                data=query.encode("utf-8"),
                headers=headers,
                timeout=30
            )

            # 如果 HTTP 狀態碼不是 200，就會跳到 except
            response.raise_for_status()

            data = response.json()
            elements = data.get("elements", [])

            for element in elements:
                place_type = classify_osm_element(element)
                counts[place_type] = counts.get(place_type, 0) + 1

                # 只保留前 30 筆，避免前端資料太大
                if len(nearby_places) < 30:
                    nearby_places.append({
                        "name": get_element_name(element),
                        "type": place_type,
                        "latitude": element.get("lat"),
                        "longitude": element.get("lon")
                    })

            facility_score = calculate_facility_score(counts)
            summary = summarize_facility_counts(counts)

            return {
                "convenience_stores": counts["convenience_store"],
                "restaurants": counts["restaurant"],
                "cafes": counts["cafe"],
                "pharmacies": counts["pharmacy"],
                "clinics": counts["clinic"],
                "laundries": counts["laundry"],
                "supermarkets": counts["supermarket"],
                "bus_stops": counts["bus_stop"],
                "facility_score": facility_score,
                "summary": summary,
                "nearby_places": nearby_places,
                "radius": radius,
                "source": f"OpenStreetMap Overpass API ({url})"
            }

        except requests.exceptions.RequestException as e:
            # 如果其中一個 endpoint 失敗，先印出錯誤，然後換下一個 endpoint
            print(f"Facility API error from {url}:", e)

    # 如果所有 endpoint 都失敗，才回傳 fallback
    return {
        "convenience_stores": 0,
        "restaurants": 0,
        "cafes": 0,
        "pharmacies": 0,
        "clinics": 0,
        "laundries": 0,
        "supermarkets": 0,
        "bus_stops": 0,
        "facility_score": 0,
        "summary": "目前無法取得附近生活機能資料，可能是公開資料 API 暫時無法使用。",
        "nearby_places": [],
        "radius": radius,
        "source": "OpenStreetMap Overpass API"
    }