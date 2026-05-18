import requests


def map_weather_code_to_text(weather_code: int) -> str:
    """
    將 Open-Meteo 回傳的 weather_code 轉成中文天氣描述。

    Open-Meteo 不會直接回傳「晴天 / 陰天 / 下雨」這種文字，
    而是回傳一個數字 code，例如：
    0 代表晴天
    1, 2, 3 代表多雲
    61, 63, 65 代表下雨

    所以我們需要自己建立一個對照表。
    """

    weather_code_map = {
        0: "晴朗",
        1: "大致晴朗",
        2: "局部多雲",
        3: "陰天",
        45: "有霧",
        48: "霧凇",
        51: "毛毛雨",
        53: "中等毛毛雨",
        55: "較強毛毛雨",
        56: "凍毛毛雨",
        57: "強凍毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "凍雨",
        67: "強凍雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "短暫小陣雨",
        81: "短暫中陣雨",
        82: "強陣雨",
        85: "短暫小雪",
        86: "短暫大雪",
        95: "雷雨",
        96: "雷雨伴隨小冰雹",
        99: "雷雨伴隨大冰雹"
    }

    # 如果遇到沒有定義的 code，就回傳「未知天氣狀況」
    return weather_code_map.get(weather_code, "未知天氣狀況")


def get_weather(latitude: float, longitude: float) -> dict:
    """
    使用 Open-Meteo API 查詢指定經緯度的即時天氣。

    這個函式會被 agent_service.py 裡面的 run_agent() 呼叫。

    輸入：
        latitude: 緯度，例如 25.0478
        longitude: 經度，例如 121.5170

    輸出：
        dict，包含溫度、天氣狀態、降雨量、風速與摘要文字。
    """

    # Open-Meteo 的天氣 API endpoint
    url = "https://api.open-meteo.com/v1/forecast"

    # API 查詢參數
    # latitude / longitude：指定查詢地點
    # current：指定要查哪些即時天氣欄位
    # timezone：設定時區，讓時間顯示為台灣時間
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "weather_code",
            "wind_speed_10m"
        ],
        "timezone": "Asia/Taipei"
    }

    try:
        # 發送 GET request 到 Open-Meteo
        # timeout=10：最多等 10 秒，避免 API 沒回應導致網站卡住
        response = requests.get(url, params=params, timeout=10)

        # 如果 HTTP 狀態碼不是 200，這行會拋出錯誤
        response.raise_for_status()

        # 將 API 回傳的 JSON 轉成 Python dict
        data = response.json()

        # Open-Meteo 的即時天氣資料會放在 current 裡
        current = data.get("current", {})

        # 取出各項資料
        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        precipitation = current.get("precipitation")
        weather_code = current.get("weather_code")
        wind_speed = current.get("wind_speed_10m")

        # 將 weather_code 轉成中文描述
        weather_text = map_weather_code_to_text(weather_code)

        # 產生一句給使用者看的摘要
        summary = (
            f"目前天氣為{weather_text}，溫度約 {temperature}°C，"
            f"濕度約 {humidity}%，降雨量約 {precipitation} mm，"
            f"風速約 {wind_speed} km/h。"
        )

        # 回傳給前端與 Summary Agent 使用的結構化資料
        return {
            "temperature": f"{temperature}°C",
            "weather": weather_text,
            "rain_probability": "目前使用降雨量資料，尚未接入降雨機率",
            "precipitation": f"{precipitation} mm",
            "humidity": f"{humidity}%",
            "wind_speed": f"{wind_speed} km/h",
            "summary": summary,
            "source": "Open-Meteo"
        }

    except requests.exceptions.RequestException as e:
        """
        如果 API 請求失敗，例如：
        - 沒網路
        - API timeout
        - API 回傳錯誤狀態碼

        我們不要讓整個系統壞掉，而是回傳一份 fallback 資料。
        這樣其他模組還可以繼續跑。
        """

        print("Weather API error:", e)

        return {
            "temperature": "未知",
            "weather": "目前無法取得天氣資料",
            "rain_probability": "未知",
            "precipitation": "未知",
            "humidity": "未知",
            "wind_speed": "未知",
            "summary": "目前天氣 API 暫時無法取得資料，建議稍後再試。",
            "source": "Open-Meteo"
        }