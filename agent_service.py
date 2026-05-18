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

def parse_rent_range(rent_range_text):
    """
    將租金範圍文字轉成數字區間。

    例如：
    "6,500 - 10,000 元/月"
    轉成：
    (6500, 10000)

    為什麼需要這個 function？
    因為 Rental Tool 回傳的是給人看的文字，
    但如果我們要判斷「房源租金是否合理」，
    就需要把文字裡面的數字抓出來比較。
    """

    # 如果資料不足，就無法解析
    if not rent_range_text or "資料不足" in rent_range_text:
        return None

    try:
        # 移除中文字與空白，只留下類似 "6500-10000"
        cleaned_text = (
            rent_range_text
            .replace("元/月", "")
            .replace(",", "")
            .replace(" ", "")
        )

        # 用 "-" 切開最低與最高租金
        parts = cleaned_text.split("-")

        if len(parts) != 2:
            return None

        min_rent = int(parts[0])
        max_rent = int(parts[1])

        return min_rent, max_rent

    except Exception:
        # 如果解析失敗，就回傳 None，避免整個系統壞掉
        return None


def get_expected_rent_range_by_room_type(rental_data, room_type):
    """
    根據房型，從 Rental Tool 回傳的 rental_data 裡面找對應的租金範圍。

    listing 的 room_type 可能是：
    - 雅房
    - 分租套房
    - 獨立套房
    - 整層合租

    rental_data 裡對應欄位是：
    - room_range
    - studio_range
    - independent_studio_range
    - shared_apartment_range
    """

    if room_type == "雅房":
        return rental_data.get("room_range")

    if room_type == "分租套房":
        return rental_data.get("studio_range")

    if room_type == "獨立套房":
        return rental_data.get("independent_studio_range")

    if room_type == "整層合租":
        return rental_data.get("shared_apartment_range")

    # 如果房型不在預期內，就回傳 None
    return None


def evaluate_rent_reasonableness(listing, rental_data):
    """
    判斷房源租金是否在合理範圍內。

    輸入：
    - listing：資料庫中的房源資料
    - rental_data：Rental Tool 根據生活圈回傳的估算租金資料

    輸出：
    - level：偏低 / 合理 / 偏高 / 資料不足
    - message：給使用者看的解釋文字
    """

    listing_rent = listing.get("rent")
    room_type = listing.get("room_type")

    # 取得此房型的市場估算範圍
    expected_range_text = get_expected_rent_range_by_room_type(
        rental_data=rental_data,
        room_type=room_type
    )

    parsed_range = parse_rent_range(expected_range_text)

    if not parsed_range:
        return {
            "level": "資料不足",
            "message": "目前缺少此房型的租金估算資料，暫時無法判斷租金是否合理。"
        }

    min_rent, max_rent = parsed_range

    # 房源租金低於估算最低值
    if listing_rent < min_rent:
        return {
            "level": "偏低",
            "message": (
                f"此房源月租為 NT$ {listing_rent:,}，低於此生活圈 {room_type} "
                f"估算範圍 NT$ {min_rent:,} - {max_rent:,}。"
                "價格看起來偏低，建議確認房況、是否有額外費用，或是否有特殊限制。"
            )
        }

    # 房源租金高於估算最高值
    if listing_rent > max_rent:
        return {
            "level": "偏高",
            "message": (
                f"此房源月租為 NT$ {listing_rent:,}，高於此生活圈 {room_type} "
                f"估算範圍 NT$ {min_rent:,} - {max_rent:,}。"
                "建議確認是否有較好的設備、坪數、管理、裝潢或地點優勢。"
            )
        }

    # 房源租金在合理範圍內
    return {
        "level": "合理",
        "message": (
            f"此房源月租為 NT$ {listing_rent:,}，位於此生活圈 {room_type} "
            f"估算範圍 NT$ {min_rent:,} - {max_rent:,} 內，租金大致合理。"
        )
    }


def generate_listing_strengths(listing, area_analysis, rent_evaluation):
    """
    根據房源條件產生優點列表。

    這裡目前是規則式 Agent。
    優點：
    - 穩定
    - 可解釋
    - 很適合 MVP

    未來可以把這些資料丟給 Gemini，產生更自然的分析。
    """

    strengths = []

    commute = area_analysis.get("commute", {})

    # 到校便利性高
    if commute.get("commute_score", 0) >= 80:
        strengths.append("到中央大學距離較近，日常上課通勤壓力較低。")

    # 租金合理
    if rent_evaluation.get("level") == "合理":
        strengths.append("租金落在目前生活圈估算範圍內，價格相對合理。")

    # 有對外窗
    if listing.get("has_window"):
        strengths.append("房間有對外窗，採光與通風條件通常較好。")

    # 包網路
    if listing.get("internet_included"):
        strengths.append("租金包含網路，對學生來說可以減少額外生活成本。")

    # 可開伙
    if listing.get("can_cook"):
        strengths.append("房源允許開伙，適合想自己煮飯、降低餐費的學生。")

    # 如果沒有任何優點被規則抓到，就給一個中性優點
    if not strengths:
        strengths.append("此房源具備基本租屋資訊，可作為看房候選之一。")

    return strengths


def generate_listing_risks(listing, area_analysis, rent_evaluation):
    """
    根據房源條件產生可能風險列表。

    風險不代表一定不好，而是提醒找房者看房時要確認。
    """

    risks = []

    commute = area_analysis.get("commute", {})

    # 到校距離偏遠
    if commute.get("commute_score", 100) < 65:
        risks.append("此房源距離中央大學較遠，若沒有機車或穩定交通方式，通勤可能較不方便。")

    # 租金偏高
    if rent_evaluation.get("level") == "偏高":
        risks.append("租金高於目前生活圈估算範圍，建議確認是否有足夠的設備或地點優勢。")

    # 租金偏低也需要注意
    if rent_evaluation.get("level") == "偏低":
        risks.append("租金低於估算範圍，建議確認房況、合約條件與是否有額外費用。")

    # 無對外窗
    if not listing.get("has_window"):
        risks.append("房間沒有對外窗，可能影響採光、通風與居住舒適度。")

    # 不包網路
    if not listing.get("internet_included"):
        risks.append("此房源不包含網路，入住前需要確認網路申辦與額外費用。")

    # 不可開伙
    if not listing.get("can_cook"):
        risks.append("此房源不可開伙，若你希望自己煮飯，可能不太適合。")

    # 電費資訊
    electricity_fee = listing.get("electricity_fee") or ""
    if "5" in electricity_fee or "6" in electricity_fee:
        risks.append("電費可能高於台電計價，夏天使用冷氣時需要特別注意電費。")

    if not risks:
        risks.append("目前沒有明顯高風險條件，但仍建議實際看房確認環境與合約。")

    return risks


def generate_questions_to_ask_landlord(listing, rent_evaluation):
    """
    根據房源資訊產生看房時要問房東的問題。

    這是 Agent 很有價值的地方：
    它不只是分析資料，還會告訴使用者下一步要問什麼。
    """

    questions = [
        "請問水電費如何計算？是否有最低收費？",
        "請問租約最短需要簽多久？押金退還規則是什麼？",
        "請問垃圾要自己追垃圾車，還是有集中垃圾區？",
        "請問晚上周邊會不會吵？附近是否有施工或車流噪音？"
    ]

    if not listing.get("internet_included"):
        questions.append("請問網路需要自己申辦嗎？每月大約多少費用？")

    if listing.get("can_cook"):
        questions.append("請問可以使用哪些烹飪設備？是否有抽油煙設備？")
    else:
        questions.append("請問是否完全不可開伙？能否使用電鍋或簡單加熱設備？")

    if listing.get("pet_allowed"):
        questions.append("請問養寵物是否需要額外清潔費或押金？")

    if rent_evaluation.get("level") in ["偏高", "偏低"]:
        questions.append("請問這個租金是否包含管理費、網路、水費或其他額外費用？")

    return questions


def decide_suitable_student_type(listing, area_analysis, rent_evaluation):
    """
    判斷這間房比較適合哪類學生。

    這個 function 會根據：
    - 到校便利性
    - 租金合理性
    - 是否可開伙
    - 是否包網路
    - 是否需要交通工具

    產生一段簡短建議。
    """

    commute = area_analysis.get("commute", {})
    commute_score = commute.get("commute_score", 0)

    if commute_score >= 80 and listing.get("rent", 999999) <= 10000:
        return "適合希望住得離學校近、通勤時間短，且預算約一萬元內的學生。"

    if commute_score < 65:
        return "比較適合有機車或能接受較長通勤時間的學生。"

    if listing.get("can_cook"):
        return "適合想自己煮飯、控制生活費，且希望有較高生活彈性的學生。"

    if rent_evaluation.get("level") == "偏高":
        return "比較適合預算較充足，且重視設備、地點或居住品質的學生。"

    return "適合正在尋找中央大學周邊一般學生租屋選項的找房者。"


def analyze_listing(listing):
    """
    真正的房源 AI 分析主入口。

    這個 function 會被 listing_detail route 呼叫。

    流程：
    1. 使用房源地址呼叫 run_agent()，取得地區分析
    2. 根據房源租金與 Rental Tool 的估算資料，判斷租金是否合理
    3. 根據房源條件產生優點、風險、適合族群、看房問題
    4. 回傳完整結構化分析結果
    """

    # 先用原本的 Agent 分析房源所在位置
    area_analysis = run_agent(listing["address"])

    # 判斷房源租金是否合理
    rent_evaluation = evaluate_rent_reasonableness(
        listing=listing,
        rental_data=area_analysis["rental"]
    )

    # 產生房源優點
    strengths = generate_listing_strengths(
        listing=listing,
        area_analysis=area_analysis,
        rent_evaluation=rent_evaluation
    )

    # 產生可能風險
    risks = generate_listing_risks(
        listing=listing,
        area_analysis=area_analysis,
        rent_evaluation=rent_evaluation
    )

    # 產生看房時要問房東的問題
    questions = generate_questions_to_ask_landlord(
        listing=listing,
        rent_evaluation=rent_evaluation
    )

    # 判斷適合哪種學生
    suitable_student_type = decide_suitable_student_type(
        listing=listing,
        area_analysis=area_analysis,
        rent_evaluation=rent_evaluation
    )

    # 產生總結文字
    final_summary = (
        f"這間「{listing['title']}」月租 NT$ {listing['rent']:,}，"
        f"房型為{listing['room_type']}。"
        f"{rent_evaluation['message']}"
        f"{area_analysis['commute']['summary']}"
        f"整體來看，{suitable_student_type}"
    )

    return {
        "area_analysis": area_analysis,
        "rent_evaluation": rent_evaluation,
        "strengths": strengths,
        "risks": risks,
        "questions": questions,
        "suitable_student_type": suitable_student_type,
        "final_summary": final_summary
    }