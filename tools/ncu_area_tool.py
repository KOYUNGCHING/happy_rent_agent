def normalize_ncu_area(user_location: str) -> dict:
    """
    將中央大學學生常用的口語地名，轉換成比較適合 Geocoding 查詢的正式地名。

    為什麼需要這個 tool？
    因為學生可能會輸入：
    - 後門
    - 中央後門
    - 宵夜街
    - 中央附近

    但這些詞不一定是 OpenStreetMap 或 Google Maps 能精準理解的地名。
    所以我們先做一層 mapping，讓 Agent 比較容易找到正確位置。
    """

    # 去除前後空白
    text = user_location.strip()

    # 中央大學周邊常見地名 mapping
    # key：使用者可能輸入的說法
    # value：比較正式、適合拿去查地圖的地名
    area_map = {
        "中央大學": "國立中央大學",
        "中央大學附近": "國立中央大學",
        "中央附近": "國立中央大學",
        "中大": "國立中央大學",
        "中大附近": "國立中央大學",
        "後門": "國立中央大學後門",
        "中央後門": "國立中央大學後門",
        "中央大學後門": "國立中央大學後門",
        "前門": "國立中央大學正門",
        "中央前門": "國立中央大學正門",
        "中央大學前門": "國立中央大學正門",
        "宵夜街": "中央大學宵夜街",
        "中央宵夜街": "中央大學宵夜街",
        "中壢火車站": "中壢車站",
        "中壢車站": "中壢車站",
        "內壢火車站": "內壢車站",
        "內壢車站": "內壢車站",
        "青埔": "桃園青埔",
        "高鐵桃園站": "高鐵桃園站"
    }

    # 如果使用者輸入剛好有在 mapping 裡，就轉成正式查詢名稱
    normalized_location = area_map.get(text, text)

    # 判斷這是不是中央大學相關生活圈
    is_ncu_related = any(keyword in text for keyword in [
        "中央", "中大", "後門", "前門", "宵夜街", "中壢", "內壢", "青埔"
    ])

    return {
        "original_location": user_location,
        "normalized_location": normalized_location,
        "is_ncu_related": is_ncu_related
    }