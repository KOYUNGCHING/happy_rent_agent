import math

NCU_LATITUDE = 24.9682
NCU_LONGITUDE = 121.1950

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine formula 計算兩個經緯度之間的直線距離。

    為什麼要用 Haversine？
    因為地球是球體，不是平面。
    如果直接用普通的歐式距離，經緯度換算會不準。
    Haversine formula 是常見的地理距離計算方式。

    注意：
    這裡算的是「直線距離」，不是實際道路距離。
    實際走路或騎車距離通常會比直線距離更長。
    """

    # 地球半徑，單位是公里
    earth_radius_km = 6371

    # 將角度轉成弧度，因為 math.sin / math.cos 使用的是弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # 緯度與經度差
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 回傳距離，單位公里
    return earth_radius_km * c


def estimate_commute_time(distance_km: float) -> dict:
    """
    根據距離估算不同交通方式到中央大學的時間。

    這裡先用簡化估算：
    - 步行速度：約 5 km/h
    - 腳踏車速度：約 12 km/h
    - 機車速度：約 25 km/h

    注意：
    這是 MVP 估算，不考慮紅綠燈、道路繞路、上下坡、停車時間。
    之後如果要更準，可以接 Google Maps Directions API 或其他路線 API。
    """

    walking_speed_kmh = 5
    bike_speed_kmh = 12
    scooter_speed_kmh = 25

    walking_minutes = distance_km / walking_speed_kmh * 60
    bike_minutes = distance_km / bike_speed_kmh * 60
    scooter_minutes = distance_km / scooter_speed_kmh * 60

    return {
        "walking_minutes": round(walking_minutes),
        "bike_minutes": round(bike_minutes),
        "scooter_minutes": round(scooter_minutes)
    }


def calculate_commute_score(distance_km: float) -> int:
    """
    根據距離計算到校便利性分數。

    分數邏輯：
    - 0.5 km 以內：非常近，95 分
    - 1 km 以內：很近，90 分
    - 2 km 以內：可接受，80 分
    - 4 km 以內：需要交通工具，65 分
    - 6 km 以內：偏遠，50 分
    - 超過 6 km：對學生日常通勤較不方便，35 分

    這個分數是為了讓 Dashboard 能快速呈現「學生租屋適合度」。
    """

    if distance_km <= 0.5:
        return 95
    elif distance_km <= 1:
        return 90
    elif distance_km <= 2:
        return 80
    elif distance_km <= 4:
        return 65
    elif distance_km <= 6:
        return 50
    else:
        return 35


def generate_commute_summary(distance_km: float, commute_time: dict, score: int) -> str:
    """
    根據距離、時間與分數產生中文摘要。
    這段摘要會顯示在前端 Dashboard 上。
    """

    if score >= 90:
        level = "非常方便"
        advice = "適合沒有機車、希望步行或騎腳踏車到校的學生。"
    elif score >= 80:
        level = "方便"
        advice = "日常到校仍算方便，騎腳踏車會比較舒服。"
    elif score >= 65:
        level = "普通"
        advice = "建議有腳踏車或機車，否則每天步行可能會比較累。"
    elif score >= 50:
        level = "偏遠"
        advice = "比較適合有機車的學生，沒有交通工具的話通勤壓力會較高。"
    else:
        level = "較不方便"
        advice = "距離中央大學較遠，不太適合需要每天到校的學生。"

    return (
        f"距離中央大學約 {distance_km:.2f} 公里，到校便利性為「{level}」。"
        f"估計步行約 {commute_time['walking_minutes']} 分鐘、"
        f"騎腳踏車約 {commute_time['bike_minutes']} 分鐘、"
        f"騎機車約 {commute_time['scooter_minutes']} 分鐘。"
        f"{advice}"
    )


def analyze_commute_to_ncu(latitude: float, longitude: float) -> dict:
    """
    分析某個地點到中央大學的通勤便利性。

    這是給 Agent 使用的主要 function。
    run_agent() 只需要呼叫這個函式，就可以拿到完整通勤分析結果。

    輸入：
        latitude: 查詢地點緯度
        longitude: 查詢地點經度

    輸出：
        dict，包含距離、估算時間、分數與摘要。
    """

    # 計算查詢地點到中央大學的直線距離
    distance_km = calculate_distance_km(
        latitude,
        longitude,
        NCU_LATITUDE,
        NCU_LONGITUDE
    )

    # 根據距離估算步行 / 腳踏車 / 機車時間
    commute_time = estimate_commute_time(distance_km)

    # 根據距離計算到校便利性分數
    commute_score = calculate_commute_score(distance_km)

    # 產生中文摘要
    summary = generate_commute_summary(
        distance_km=distance_km,
        commute_time=commute_time,
        score=commute_score
    )

    return {
        "distance_km": round(distance_km, 2),
        "walking_minutes": commute_time["walking_minutes"],
        "bike_minutes": commute_time["bike_minutes"],
        "scooter_minutes": commute_time["scooter_minutes"],
        "commute_score": commute_score,
        "summary": summary,
        "method": "Haversine straight-line distance"
    }