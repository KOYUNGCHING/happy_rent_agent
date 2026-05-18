import csv
import os


def get_checklist_csv_path() -> str:
    """
    取得 viewing_checklist.csv 的完整路徑。

    這樣寫可以避免因為執行位置不同，導致程式找不到 CSV。
    """

    current_file_path = os.path.abspath(__file__)
    tools_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(tools_dir)

    return os.path.join(project_root, "data", "viewing_checklist.csv")


def load_viewing_checklist() -> list:
    """
    讀取看房 Checklist CSV。

    回傳格式：
    [
        {
            "category": "房間情況",
            "question": "櫃子是否有發霉",
            "reason": "發霉可能代表房間潮濕或通風不良"
        },
        ...
    ]
    """

    csv_path = get_checklist_csv_path()

    if not os.path.exists(csv_path):
        print(f"Checklist CSV not found: {csv_path}")
        return []

    checklist = []

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            checklist.append(row)

    return checklist


def generate_smart_checklist(listing: dict) -> list:
    """
    根據房源條件，產生比較適合這間房的看房提醒。

    目前 MVP 做法：
    1. 先讀取所有 checklist
    2. 根據房源條件加強某些提醒
    3. 回傳前 8~12 個最重要問題

    未來可以升級：
    - 用 Gemini 根據 listing 自動挑選問題
    - 根據使用者偏好產生個人化 checklist
    """

    checklist = load_viewing_checklist()

    if not checklist:
        return [
            {
                "category": "基本檢查",
                "question": "確認房間採光、通風、水電費與租約條件。",
                "reason": "目前 checklist 資料不足，先提供基本提醒。"
            }
        ]

    selected_items = []

    # --------------------------------------------------------
    # 基本必問問題：不管什麼房源都建議問
    # --------------------------------------------------------
    important_keywords = [
        "押金",
        "房租",
        "水電費",
        "租約",
        "垃圾",
        "熱水",
        "排水",
        "發霉"
    ]

    for item in checklist:
        question = item.get("question", "")

        if any(keyword in question for keyword in important_keywords):
            selected_items.append(item)

    # --------------------------------------------------------
    # 根據房源條件加強提醒
    # --------------------------------------------------------

    # 如果不包網路，就加入網路費問題
    if not listing.get("internet_included"):
        selected_items.extend([
            item for item in checklist
            if "網路" in item.get("question", "")
        ])

    # 如果不可開伙，就加入開火 / 快煮鍋問題
    if not listing.get("can_cook"):
        selected_items.extend([
            item for item in checklist
            if "開火" in item.get("question", "") or "快煮鍋" in item.get("question", "")
        ])

    # 如果房源描述或地址提到潮濕、舊、木門，就加強濕氣與霉味檢查
    description = listing.get("description") or ""
    address = listing.get("address") or ""
    text = description + address

    if "濕" in text or "舊" in text or "木門" in text:
        selected_items.extend([
            item for item in checklist
            if "潮濕" in item.get("reason", "") or "發霉" in item.get("question", "") or "霉味" in item.get("question", "")
        ])

    # 如果地址或描述提到較遠，就加入停車與通勤問題
    if "遠" in text or "中壢" in text or "青埔" in text:
        selected_items.extend([
            item for item in checklist
            if item.get("category") == "車位"
        ])

    # --------------------------------------------------------
    # 去除重複問題
    # --------------------------------------------------------
    unique_items = []
    seen_questions = set()

    for item in selected_items:
        question = item.get("question")

        if question not in seen_questions:
            unique_items.append(item)
            seen_questions.add(question)

    # 最多回傳 12 題，避免畫面太長
    return unique_items[:12]