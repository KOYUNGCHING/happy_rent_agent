import csv
import math
import os
import requests

from dotenv import load_dotenv


# 取得目前檔案位置：tools/air_quality_tool.py
current_file_path = os.path.abspath(__file__)

# 取得 tools 資料夾
tools_dir = os.path.dirname(current_file_path)

# 取得專案根目錄 happy_rent_agent
project_root = os.path.dirname(tools_dir)

# 明確指定 .env 路徑
env_path = os.path.join(project_root, ".env")

# 載入 .env
load_dotenv(env_path)
AQI_API_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_432"

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine formula 計算兩個經緯度之間的距離。

    為什麼需要？
    因為環境部 AQI 資料是「測站」資料，
    但使用者輸入的是租屋地點。
    所以我們要找「離租屋地點最近的測站」。
    """

    earth_radius_km = 6371

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_km * c


def safe_float(value):
    """
    將字串轉成 float。

    AQI API 回傳的 latitude / longitude / PM2.5 有時候可能是：
    - 空字串
    - None
    - 非數字

    如果直接 float(value) 可能會壞掉，
    所以寫一個 safe_float 來保護。
    """

    try:
        if value is None or value == "":
            return None

        return float(value)

    except ValueError:
        return None


def safe_int(value):
    """
    將字串轉成 int。

    AQI 可能是 "68" 這種字串。
    如果資料缺失，就回傳 None。
    """

    try:
        if value is None or value == "":
            return None

        return int(float(value))

    except ValueError:
        return None


def get_aqi_level(aqi: int) -> str:
    """
    根據 AQI 數值轉成中文等級。

    台灣常見 AQI 等級：
    0-50：良好
    51-100：普通
    101-150：對敏感族群不健康
    151-200：對所有族群不健康
    201-300：非常不健康
    301+：危害
    """

    if aqi is None:
        return "未知"

    if aqi <= 50:
        return "良好"

    if aqi <= 100:
        return "普通"

    if aqi <= 150:
        return "對敏感族群不健康"

    if aqi <= 200:
        return "對所有族群不健康"

    if aqi <= 300:
        return "非常不健康"

    return "危害"


def generate_air_quality_summary(station_name: str, distance_km: float, aqi: int, level: str, pm25: str) -> str:
    """
    產生給使用者看的空氣品質摘要。
    """

    if aqi is None:
        return (
            f"最近測站為 {station_name}，距離約 {distance_km:.1f} 公里，"
            "但目前 AQI 資料不足，建議稍後再查詢。"
        )

    if level == "良好":
        advice = "空氣品質良好，對一般日常生活影響較小。"
    elif level == "普通":
        advice = "空氣品質普通，對一般族群影響不大，但敏感族群仍可留意。"
    elif level == "對敏感族群不健康":
        advice = "敏感族群如氣喘、過敏或呼吸道較敏感者，外出時需要多注意。"
    elif level == "對所有族群不健康":
        advice = "空氣品質較差，建議減少長時間戶外活動。"
    else:
        advice = "空氣品質不佳，建議避免長時間戶外活動並注意健康。"

    return (
        f"最近空氣品質測站為 {station_name}，距離約 {distance_km:.1f} 公里。"
        f"目前 AQI 約為 {aqi}，等級為「{level}」，PM2.5 約為 {pm25}。"
        f"{advice}"
    )

def fetch_aqi_records() -> list:
    """
    從環境部 API 取得 AQI 測站資料。

    這版會使用 .env 裡的 MOENV_API_KEY。

    流程：
    1. 從 .env 讀取 MOENV_API_KEY
    2. 帶著 api_key 呼叫環境部 AQI API
    3. 如果成功，回傳 records
    4. 如果失敗，例如 SSL、API key、網路錯誤，就改用本地 fallback CSV

    注意：
    API key 可以解決授權問題，
    但如果你的 Python 3.13 仍然遇到 SSL 憑證驗證錯誤，
    還是會進入 fallback。
    """

    # 從 .env 讀取環境部 API key
    api_key = os.getenv("MOENV_API_KEY")

    # 如果沒有讀到 key，提醒開發者，但仍然使用 fallback
    if not api_key:
        print("MOENV_API_KEY not found in .env. Using local fallback CSV.")
        return load_local_aqi_records()

    params = {
        "format": "json",
        "limit": 1000,
        "sort": "ImportDate desc",
        "api_key": api_key
    }

    headers = {
        "User-Agent": "happy-rent-agent/1.0 (student project)",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            AQI_API_URL,
            params=params,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        records = data.get("records", [])

        if records:
            return records

        print("AQI API returned no records. Using local fallback CSV.")
        return load_local_aqi_records()

    except requests.exceptions.SSLError as e:
        print("AQI API SSL error. Using local fallback CSV:", e)
        return load_local_aqi_records()

    except requests.exceptions.RequestException as e:
        print("AQI API request error. Using local fallback CSV:", e)
        return load_local_aqi_records()

    except Exception as e:
        print("AQI API unknown error. Using local fallback CSV:", e)
        return load_local_aqi_records()

def get_local_aqi_csv_path() -> str:
    """
    取得本地 AQI fallback CSV 的路徑。

    fallback 的目的是：
    如果環境部 API 因為 SSL、網路、API key 問題失敗，
    系統仍可以用本地 sample data 完成 demo。
    """

    current_file_path = os.path.abspath(__file__)
    tools_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(tools_dir)

    return os.path.join(project_root, "data", "taiwan_aqi_sample.csv")


def load_local_aqi_records() -> list:
    """
    從本地 CSV 讀取 AQI 測站資料。

    注意：
    這不是即時資料，只是 API 失敗時的 demo fallback。
    """

    csv_path = get_local_aqi_csv_path()

    if not os.path.exists(csv_path):
        print(f"Local AQI CSV not found: {csv_path}")
        return []

    records = []

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            records.append(row)

    return records


def find_nearest_station(latitude: float, longitude: float, records: list) -> dict:
    """
    從所有 AQI 測站資料中，找出距離使用者地點最近的測站。
    """

    nearest_station = None
    nearest_distance = None

    for record in records:
        # 環境部資料欄位常見是 latitude / longitude
        # 有時也可能是 lat / lon，所以這裡多做一點保護
        station_lat = safe_float(
            record.get("latitude")
            or record.get("lat")
            or record.get("Latitude")
        )

        station_lon = safe_float(
            record.get("longitude")
            or record.get("lon")
            or record.get("Longitude")
        )

        # 如果這筆測站沒有座標，就跳過
        if station_lat is None or station_lon is None:
            continue

        distance = calculate_distance_km(
            latitude,
            longitude,
            station_lat,
            station_lon
        )

        if nearest_distance is None or distance < nearest_distance:
            nearest_distance = distance
            nearest_station = record

    if nearest_station is None:
        return None

    nearest_station["_distance_km"] = nearest_distance

    return nearest_station


def get_air_quality(latitude: float, longitude: float) -> dict:
    """
    查詢指定地點附近的空氣品質。

    這是給 Agent 使用的主要 function。

    流程：
    1. 從環境部 API 取得所有測站資料
    2. 找出距離輸入座標最近的測站
    3. 取得該測站 AQI / PM2.5 / PM10 / 狀態
    4. 回傳前端與 AI Summary 使用的結構化資料
    """

    try:
        records = fetch_aqi_records()

        nearest_station = find_nearest_station(
            latitude=latitude,
            longitude=longitude,
            records=records
        )

        if nearest_station is None:
            raise ValueError("找不到附近空氣品質測站")

        station_name = (
            nearest_station.get("sitename")
            or nearest_station.get("site_name")
            or nearest_station.get("SiteName")
            or "未知測站"
        )

        county = (
            nearest_station.get("county")
            or nearest_station.get("County")
            or "未知縣市"
        )

        aqi = safe_int(
            nearest_station.get("aqi")
            or nearest_station.get("AQI")
        )

        pm25 = (
            nearest_station.get("pm2.5")
            or nearest_station.get("pm25")
            or nearest_station.get("PM2.5")
            or "未知"
        )

        pm10 = (
            nearest_station.get("pm10")
            or nearest_station.get("PM10")
            or "未知"
        )

        status = (
            nearest_station.get("status")
            or nearest_station.get("Status")
            or get_aqi_level(aqi)
        )

        pollutant = (
            nearest_station.get("pollutant")
            or nearest_station.get("Pollutant")
            or "未知"
        )

        publish_time = (
            nearest_station.get("publishtime")
            or nearest_station.get("PublishTime")
            or "未知"
        )

        distance_km = nearest_station.get("_distance_km", 0)

        level = get_aqi_level(aqi)

        summary = generate_air_quality_summary(
            station_name=station_name,
            distance_km=distance_km,
            aqi=aqi,
            level=level,
            pm25=pm25
        )

        return {
            "aqi": aqi,
            "level": level,
            "status": status,
            "pm25": pm25,
            "pm10": pm10,
            "pollutant": pollutant,
            "station_name": station_name,
            "county": county,
            "distance_km": round(distance_km, 2),
            "publish_time": publish_time,
            "summary": summary,
            "source": "環境部空氣品質指標 AQI 開放資料"
        }

    except Exception as e:
        """
        如果 API 失敗，不要讓整個 Agent 壞掉。

        可能原因：
        - API 暫時無法使用
        - 網路問題
        - 欄位格式改變
        - 查不到最近測站
        """

        print("Air Quality API error:", e)

        return {
            "aqi": None,
            "level": "未知",
            "status": "目前無法取得",
            "pm25": "未知",
            "pm10": "未知",
            "pollutant": "未知",
            "station_name": "未知測站",
            "county": "未知縣市",
            "distance_km": None,
            "publish_time": "未知",
            "summary": "目前無法取得真實空氣品質資料，可能是公開資料 API 暫時無法使用。",
            "source": "環境部空氣品質指標 AQI 開放資料"
        }