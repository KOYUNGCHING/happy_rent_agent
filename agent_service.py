from tools.geocode_tool import geocode_location
from tools.weather_tool import get_weather
from tools.air_quality_tool import get_air_quality
from tools.transport_tool import get_transport_info
from tools.facility_tool import get_facilities
from tools.rental_tool import get_rental_data


def summarize_area(location, weather, air_quality, transport, facilities, rental):
    """
    Template-based summary for MVP.
    Later this can be replaced by Gemini / LLM summary generation.
    """
    summary = (
        f"{location['location_name']}附近屬於交通便利、生活機能完整，但租金相對偏高的區域。"
        f"此區位於{location['city']}{location['district']}，附近有捷運、公車、YouBike 等交通資源，"
        f"適合重視通勤效率的租屋族。不過，由於人流量與商業活動較多，可能會有租金偏高、環境較吵的問題。"
    )

    pros = [
        "交通非常便利，適合需要通勤或常移動的人",
        "生活機能完整，外食、採買與醫療資源都方便",
        "附近公共設施多，日常生活便利性高"
    ]

    cons = [
        "租金相對偏高，可能不適合預算有限的租屋族",
        "人流量較大，部分區域可能較吵",
        "熱門地區競爭高，看房決策時間可能較短"
    ]

    suitable_for = [
        "重視交通便利的學生或上班族",
        "需要經常搭乘捷運、火車或高鐵的人",
        "預算較充足且希望生活機能完整的租屋族"
    ]

    suggestion = (
        f"如果你最重視交通與生活便利性，{location['location_name']}附近是很適合考慮的區域。"
        f"但如果你希望租金較低或居住環境更安靜，建議可以比較附近其他區域。"
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
    location_name = extract_location(user_input)

    location = geocode_location(location_name)
    weather = get_weather(location["latitude"], location["longitude"])
    air_quality = get_air_quality(location["latitude"], location["longitude"])
    transport = get_transport_info(location["latitude"], location["longitude"])
    facilities = get_facilities(location["latitude"], location["longitude"])
    rental = get_rental_data(location["city"], location["district"])

    ai_analysis = summarize_area(
        location=location,
        weather=weather,
        air_quality=air_quality,
        transport=transport,
        facilities=facilities,
        rental=rental
    )

    return {
        "location": location,
        "weather": weather,
        "air_quality": air_quality,
        "transport": transport,
        "facilities": facilities,
        "rental": rental,
        "ai_analysis": ai_analysis
    }


def chat_with_agent(message, current_area_data=None):
    """
    Simple chatbot response for MVP.
    Later this can be replaced by Gemini with conversation memory.
    """
    if current_area_data:
        location_name = current_area_data["location"]["location_name"]

        if "為什麼" in message and "租金" in message:
            return (
                f"{location_name}租金偏高的主要原因通常是交通便利、商業活動密集、生活機能完整，"
                "再加上捷運與主要車站周邊需求高，所以租屋價格容易高於一般住宅區。"
            )

        if "適合" in message:
            return (
                f"{location_name}比較適合重視交通便利、生活機能和通勤效率的人。"
                "如果你預算有限或希望環境安靜，建議再比較附近其他區域。"
            )

        if "注意" in message or "checklist" in message:
            return (
                "看房時建議注意：晚上是否吵、實際步行到捷運站時間、水壓是否穩定、"
                "房間採光與通風、附近是否有垃圾集中區，以及尖峰時段周邊是否擁擠。"
            )

    return (
        "你可以問我：這個地區適合租屋嗎？為什麼租金偏高？看房要注意什麼？"
        "或直接輸入一個地點讓我幫你分析。"
    )