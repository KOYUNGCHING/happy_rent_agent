from tools.geocode_tool import geocode_location
from tools.weather_tool import get_weather
from tools.air_quality_tool import get_air_quality
from tools.transport_tool import get_transport_info
from tools.facility_tool import get_facilities
from tools.rental_tool import get_rental_data
from tools.ncu_area_tool import normalize_ncu_area
from tools.commute_tool import analyze_commute_to_ncu


def summarize_area(location, weather, air_quality, commute, transport, facilities, rental):
    """
    Template-based summary for MVP.
    Later this can be replaced by Gemini / LLM summary generation.
    """
    summary = (
        f"{location['location_name']}附近是中央大學學生可考慮的租屋區域之一。"
        f"此區位於{location['city']}{location['district']}，"
        f"{commute['summary']}"
        f"生活機能方面，{facilities['summary']}"
        f"租金方面，{rental['summary']}"
    )

    # 針對中央大學學生租屋情境整理優點
    pros = [
        f"到中央大學距離約 {commute['distance_km']} 公里，可作為學生租屋距離判斷依據",
        "可根據步行、腳踏車與機車時間評估是否適合日常通勤",
        "系統會同時整合租金、生活機能、天氣與空氣品質，減少學生手動查詢時間"
    ]
    # 針對中央大學學生租屋情境整理可能缺點
    cons = [
        "目前租金資料為 MVP 估算，尚未接入即時租屋平台或校園租屋資料庫",
        "通勤時間目前使用直線距離估算，實際時間可能受道路、紅綠燈與交通方式影響",
        "生活機能目前仍是基礎版本，後續需要加入學生常用設施，例如洗衣店、宵夜、影印店與機車行"
    ]
    # 針對中央大學學生整理適合族群
    suitable_for = [
        "正在尋找中央大學校外租屋的學生",
        "想快速比較不同生活圈到校便利性的學生",
        "希望在看房前先了解租金、通勤與生活機能的租屋族"
    ]

    suggestion = (
        f"如果你是中央大學學生，選擇{location['location_name']}附近租屋時，"
        f"最需要考慮的是到校距離、是否有交通工具、生活機能與租金負擔。"
        f"{commute['summary']}"
    )

    return {
        "summary": summary,
        "pros": pros,
        "cons": cons,
        "suitable_for": suitable_for,
        "suggestion": suggestion
    }


def extract_location(user_input):
    """
    Very simple location extraction for MVP.
    Later this can be replaced by an LLM-based input parser.
    """
    text = user_input.strip()

    remove_words = [
        "我想在",
        "我想住在",
        "我想找",
        "附近租房子",
        "附近租屋",
        "租房子",
        "租屋",
        "附近",
        "幫我分析",
        "分析"
    ]

    for word in remove_words:
        text = text.replace(word, "")

    return text.strip() if text.strip() else user_input.strip()


def run_agent(user_input):
    """
    Main function used by both Web App and future LINE Bot.
    """
    # 先從使用者輸入中抽取地點名稱
    location_name = extract_location(user_input)

    # 將中央大學學生常用的口語地名轉成正式地名
    # 例如：「後門」→「國立中央大學後門」
    ncu_area = normalize_ncu_area(location_name)

    # 使用轉換後的正式地名去做 Geocoding
    location = geocode_location(ncu_area["normalized_location"])

    # 把原始輸入與是否為中央大學生活圈也存進 location
    # 這樣前端或 Summary Agent 之後可以使用
    location["original_location"] = ncu_area["original_location"]
    location["normalized_location"] = ncu_area["normalized_location"]
    location["is_ncu_related"] = ncu_area["is_ncu_related"]
    weather = get_weather(location["latitude"], location["longitude"])
    # 分析查詢地點到中央大學的距離與通勤時間
    # 這是新版中央大學學生租屋 Agent 的核心功能之一
    commute = analyze_commute_to_ncu(
        location["latitude"],
        location["longitude"]
    )
    air_quality = get_air_quality(location["latitude"], location["longitude"])
    transport = get_transport_info(location["latitude"], location["longitude"])
    facilities = get_facilities(location["latitude"], location["longitude"])
    # 根據中央大學學生租屋情境取得租金估算
    # 這裡會把地點名稱與到中央大學距離傳進去
    # Rental Tool 會依照不同生活圈給出不同租金範圍
    rental = get_rental_data(
        city=location["city"],
        district=location["district"],
        location_name=location["location_name"],
        distance_km=commute["distance_km"]
    )

    ai_analysis = summarize_area(
        location=location,
        weather=weather,
        air_quality=air_quality,
        commute=commute,
        transport=transport,
        facilities=facilities,
        rental=rental
    )

    return {
        "location": location,
        "weather": weather,
        "air_quality": air_quality,
        "commute": commute,
        "transport": transport,
        "facilities": facilities,
        "rental": rental,
        "ai_analysis": ai_analysis
    }


def chat_with_agent(message, current_area_data=None):
    """
    簡易版 Chatbot 回覆邏輯。

    這裡目前還不是 LLM，而是用關鍵字判斷。
    好處是穩定、可控，也很適合 MVP。
    之後可以改成 Gemini，讓它根據 current_area_data 自然回答。
    """

    if current_area_data:
        location_name = current_area_data["location"]["location_name"]

        # 取得 commute 資訊
        # get() 可以避免資料不存在時程式壞掉
        commute = current_area_data.get("commute", {})

        if "沒有機車" in message or "走路" in message or "腳踏車" in message or "通勤" in message:
            return (
                f"{location_name}到中央大學的距離約 {commute.get('distance_km', '未知')} 公里。"
                f"估計步行約 {commute.get('walking_minutes', '未知')} 分鐘，"
                f"騎腳踏車約 {commute.get('bike_minutes', '未知')} 分鐘，"
                f"騎機車約 {commute.get('scooter_minutes', '未知')} 分鐘。"
                f"{commute.get('summary', '')}"
            )

        if "租金" in message or "房租" in message or "多少錢" in message:
            rental = current_area_data.get("rental", {})

            return (
                f"{location_name}的租金負擔等級目前估計為「{rental.get('rental_level', '未知')}」。"
                f"雅房約 {rental.get('room_range', '資料不足')}，"
                f"分租套房約 {rental.get('studio_range', '資料不足')}，"
                f"獨立套房約 {rental.get('independent_studio_range', '資料不足')}。"
                f"{rental.get('student_advice', '')}"
                "提醒：目前這是 MVP 估算資料，之後可以接入實際租屋資料集提高準確度。"
            )


        if "適合" in message:
            return (
                f"{location_name}是否適合中央大學學生，主要要看你有沒有交通工具與預算。"
                f"{commute.get('summary', '')}"
            )

        if "注意" in message or "checklist" in message:
            return (
                "中央大學附近看房時建議注意：晚上是否吵、到學校實際通勤時間、"
                "是否有自助洗衣、垃圾處理方式、水電費計算、網路是否包含、"
                "房間通風採光，以及下雨天到校是否方便。"
            )

    return (
        "你可以問我：這個地區適合中央大學學生嗎？沒有機車方便嗎？"
        "走路到學校要多久？或看房要注意什麼？"
    )