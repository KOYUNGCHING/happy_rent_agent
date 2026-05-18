import json
import os

from dotenv import load_dotenv
from google import genai


# ============================================================
# 明確載入專案根目錄的 .env
# ============================================================
# 這樣不管你從哪個資料夾執行 Flask，
# 都比較能穩定讀到 GEMINI_API_KEY。
# ============================================================

current_file_path = os.path.abspath(__file__)
tools_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(tools_dir)
env_path = os.path.join(project_root, ".env")

load_dotenv(env_path)


def get_gemini_client():
    """
    建立 Gemini client。

    為什麼要包成 function？
    因為如果 GEMINI_API_KEY 沒設定，
    我們可以在這裡統一處理錯誤，而不是讓整個 app 直接壞掉。
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")

    # Google Gen AI SDK client
    return genai.Client(api_key=api_key)


def build_area_summary_prompt(area_data: dict) -> str:
    """
    建立「租屋區域分析」的 Gemini prompt。

    area_data 會包含：
    - location
    - weather
    - air_quality
    - commute
    - facilities
    - rental

    我們把資料整理成 JSON 給 Gemini，
    要求它根據資料產生學生看得懂的租屋建議。
    """

    area_json = json.dumps(
        area_data,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
你是一個專門協助中央大學學生找房的 AI 租屋助理。

請根據以下工具回傳的結構化資料，產生一份「中央大學學生租屋區域分析」。

請遵守：
1. 不要假裝知道資料中沒有的內容。
2. 如果資料來源是 fallback 或 sample data，要提醒使用者資料可能不是即時資料。
3. 語氣要像給學生看的實用建議，不要太官方。
4. 請重點分析：
   - 到中央大學是否方便
   - 沒有機車是否適合
   - 租金負擔
   - 生活機能
   - 天氣與空氣品質
   - 適合哪種學生
   - 看房前要注意什麼

請輸出格式：

## 整體判斷
一段 3-5 句的總結。

## 優點
- ...
- ...
- ...

## 可能缺點
- ...
- ...
- ...

## 適合族群
- ...

## 看房提醒
- ...

以下是工具資料：
{area_json}
"""
    return prompt


def generate_area_summary_with_gemini(area_data: dict) -> dict:
    """
    使用 Gemini 產生區域分析摘要。

    回傳格式：
    {
        "enabled": True,
        "summary_text": "...",
        "source": "Gemini"
    }

    如果 Gemini 失敗，回傳 enabled=False，
    讓主程式可以 fallback 到原本規則式摘要。
    """

    try:
        client = get_gemini_client()

        prompt = build_area_summary_prompt(area_data)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            "enabled": True,
            "summary_text": response.text,
            "source": "Gemini 2.5 Flash"
        }

    except Exception as e:
        print("Gemini area summary error:", e)

        return {
            "enabled": False,
            "summary_text": "",
            "source": "Rule-based fallback"
        }


def build_listing_summary_prompt(listing: dict, listing_analysis: dict) -> str:
    """
    建立「單一房源分析」的 Gemini prompt。

    listing：房東上架的房源資料
    listing_analysis：規則式 Agent 已經分析出的結果
    """

    listing_json = json.dumps(
        listing,
        ensure_ascii=False,
        indent=2
    )

    analysis_json = json.dumps(
        listing_analysis,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
你是一個專門協助中央大學學生看房的 AI 租屋助理。

請根據以下「房源資料」與「工具分析結果」，產生一份單一房源的租屋建議。

請遵守：
1. 不要編造資料。
2. 如果資料中沒有提到，就說「需要看房時確認」。
3. 你的建議要實用，像學長姐提醒學弟妹看房。
4. 請特別注意：
   - 租金是否合理
   - 到中央大學是否方便
   - 沒有機車是否適合
   - 水電費與網路是否需要注意
   - 房間設備風險
   - 看房時一定要問房東什麼

請輸出格式：

## 這間房適合你嗎？
一段總結。

## 主要優點
- ...
- ...

## 需要注意的風險
- ...
- ...

## 看房時必問
- ...
- ...

房源資料：
{listing_json}

工具分析結果：
{analysis_json}
"""
    return prompt


def generate_listing_summary_with_gemini(listing: dict, listing_analysis: dict) -> dict:
    """
    使用 Gemini 產生單一房源分析摘要。

    如果失敗，就回傳 fallback。
    """

    try:
        client = get_gemini_client()

        prompt = build_listing_summary_prompt(
            listing=listing,
            listing_analysis=listing_analysis
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            "enabled": True,
            "summary_text": response.text,
            "source": "Gemini 2.5 Flash"
        }

    except Exception as e:
        print("Gemini listing summary error:", e)

        return {
            "enabled": False,
            "summary_text": "",
            "source": "Rule-based fallback"
        }