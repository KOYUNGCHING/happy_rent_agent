import csv
import os


def classify_rental_area(location_name: str, distance_km: float) -> str:
    """
    根據地點名稱與距離中央大學的遠近，判斷租屋區域類型。

    這個分類會用來決定要讀取 CSV 裡哪一種 area_type 的租金資料。

    例如：
    - ncu_core：中央大學核心生活圈
    - zhongli_station：中壢車站生活圈
    - neili：內壢生活圈
    - qingpu：青埔生活圈
    """

    # 避免 location_name 是 None 導致程式錯誤
    location_name = location_name or ""

    # 中文不需要 lower，但如果未來有英文輸入，保留這個習慣
    name = location_name.lower()

    # 中央大學核心生活圈
    if (
        "中央" in location_name
        or "中大" in location_name
        or "後門" in location_name
        or "前門" in location_name
        or "宵夜街" in location_name
        or distance_km <= 2
    ):
        return "ncu_core"

    # 中壢車站生活圈
    if "中壢" in location_name or "zhongli" in name:
        return "zhongli_station"

    # 內壢生活圈
    if "內壢" in location_name or "neili" in name:
        return "neili"

    # 青埔 / 高鐵桃園站生活圈
    if "青埔" in location_name or "高鐵" in location_name or "qingpu" in name:
        return "qingpu"

    # 如果地名沒有明顯關鍵字，就用距離中央大學遠近來判斷
    if distance_km <= 3:
        return "near_ncu"
    elif distance_km <= 6:
        return "medium_distance"
    else:
        return "far_from_ncu"


def get_csv_path() -> str:
    """
    取得 ncu_rental_estimates.csv 的絕對路徑。

    為什麼要這樣寫？
    因為如果直接寫 "data/ncu_rental_estimates.csv"，
    有時候會受到你執行 python app.py 的位置影響。

    用 __file__ 可以取得目前這個 rental_tool.py 的位置，
    再往上一層找到專案根目錄，最後組合出 data CSV 的路徑。
    """

    # 目前檔案位置，例如：
    # /Users/xxx/Desktop/happy_rent_agent/tools/rental_tool.py
    current_file_path = os.path.abspath(__file__)

    # tools 資料夾位置
    tools_dir = os.path.dirname(current_file_path)

    # 專案根目錄，也就是 tools 的上一層
    project_root = os.path.dirname(tools_dir)

    # 組合出 CSV 完整路徑
    csv_path = os.path.join(project_root, "data", "ncu_rental_estimates.csv")

    return csv_path


def load_rental_dataset() -> list:
    """
    讀取中央大學租屋估算 CSV 資料。

    回傳格式：
    [
        {
            "area_type": "ncu_core",
            "area_name": "中央大學核心生活圈",
            "room_type": "雅房",
            "min_rent": "4500",
            "max_rent": "7000",
            ...
        },
        ...
    ]

    注意：
    csv.DictReader 會把每一列資料轉成 dict。
    欄位名稱會來自 CSV 第一列的 header。
    """

    csv_path = get_csv_path()

    # 如果找不到 CSV，直接回傳空 list
    # 後面 get_rental_data() 會處理 fallback
    if not os.path.exists(csv_path):
        print(f"Rental CSV not found: {csv_path}")
        return []

    rows = []

    # encoding="utf-8-sig" 可以避免某些 CSV 開頭 BOM 導致欄位名稱怪掉
    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


def format_rent_range(min_rent: int, max_rent: int, room_type: str) -> str:
    """
    將 min_rent / max_rent 轉成前端要看的文字格式。

    如果 min_rent 或 max_rent 是 0，代表該房型資料不足或該區較少此房型。
    """

    if min_rent <= 0 or max_rent <= 0:
        return "資料不足或較少此類物件"

    # :, 會把數字加上千分位，例如 10000 -> 10,000
    return f"{min_rent:,} - {max_rent:,} 元/月"


def summarize_rental_rows(rows: list, area_type: str) -> dict:
    """
    將同一個 area_type 的多筆房型資料整理成前端需要的格式。

    CSV 是一列一個房型：
    - 雅房
    - 分租套房
    - 獨立套房
    - 整層合租

    但前端想要的是：
    {
        "room_range": "...",
        "studio_range": "...",
        "independent_studio_range": "...",
        "shared_apartment_range": "..."
    }

    所以這裡要做資料整理。
    """

    # 先篩選出符合 area_type 的資料
    matched_rows = [
        row for row in rows
        if row.get("area_type") == area_type
    ]

    # 如果找不到對應 area_type，就回傳 None，讓外層做 fallback
    if not matched_rows:
        return None

    # 預設值
    rental_level = matched_rows[0].get("rental_level", "資料不足")
    area_name = matched_rows[0].get("area_name", "未知生活圈")
    summary = matched_rows[0].get("summary", "目前缺少租屋摘要資料。")
    student_advice = matched_rows[0].get("student_advice", "目前缺少學生租屋建議。")

    # 建立房型對應表
    rent_ranges = {
        "雅房": "資料不足",
        "分租套房": "資料不足",
        "獨立套房": "資料不足",
        "整層合租": "資料不足"
    }

    # 逐列處理每一個房型
    for row in matched_rows:
        room_type = row.get("room_type", "")

        # CSV 讀進來會是字串，所以要轉成 int
        # 如果資料缺失，就當作 0
        min_rent = int(row.get("min_rent") or 0)
        max_rent = int(row.get("max_rent") or 0)

        rent_ranges[room_type] = format_rent_range(
            min_rent=min_rent,
            max_rent=max_rent,
            room_type=room_type
        )

    return {
        "rental_level": rental_level,
        "area_type": area_type,
        "area_name": area_name,
        "room_range": rent_ranges["雅房"],
        "studio_range": rent_ranges["分租套房"],
        "independent_studio_range": rent_ranges["獨立套房"],
        "shared_apartment_range": rent_ranges["整層合租"],
        "summary": summary,
        "student_advice": student_advice,
        "note": "目前為 MVP 估算資料，非即時租屋平台價格。"
    }


def get_fallback_rental_data(area_type: str) -> dict:
    """
    當 CSV 找不到或讀取失敗時，提供 fallback 資料。

    這樣做的好處：
    即使資料檔案不小心遺失，網站也不會整個壞掉。
    """

    return {
        "rental_level": "資料不足",
        "area_type": area_type,
        "area_name": "未知生活圈",
        "room_range": "資料不足",
        "studio_range": "資料不足",
        "independent_studio_range": "資料不足",
        "shared_apartment_range": "資料不足",
        "summary": "目前缺少此區租屋估算資料。",
        "student_advice": "建議補充中央大學周邊租屋資料集，或改用使用者回報資料。",
        "note": "目前為 fallback 資料，請確認 CSV 是否存在。"
    }


def get_rental_data(
    city: str,
    district: str,
    location_name: str = "",
    distance_km: float = None
) -> dict:
    """
    取得中央大學學生租屋情境的租金估算資料。

    這個 function 是 Rental Tool 對外主要入口。
    agent_service.py 只需要呼叫這個 function。

    流程：
    1. 根據地點名稱與距離判斷 area_type
    2. 讀取 CSV 租屋資料
    3. 根據 area_type 找出對應資料
    4. 整理成前端需要的 JSON 格式
    """

    # 如果 distance_km 沒有傳進來，給一個很大的值
    # 避免 classify_rental_area() 比較距離時壞掉
    if distance_km is None:
        distance_km = 999

    # 判斷生活圈類型
    area_type = classify_rental_area(
        location_name=location_name,
        distance_km=distance_km
    )

    # 讀取 CSV 資料
    rows = load_rental_dataset()

    # 如果 CSV 沒有資料，回傳 fallback
    if not rows:
        return get_fallback_rental_data(area_type)

    # 從 CSV 裡整理出對應生活圈的租金資料
    rental_data = summarize_rental_rows(
        rows=rows,
        area_type=area_type
    )

    # 如果找不到對應 area_type，也回傳 fallback
    if rental_data is None:
        return get_fallback_rental_data(area_type)

    # 額外加入 city / district，之後如果前端要顯示可以用
    rental_data["city"] = city
    rental_data["district"] = district

    return rental_data