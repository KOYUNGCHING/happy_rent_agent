import csv
import os
from database import get_db_connection


def get_private_csv_path():
    """
    取得 private_listings_notes.csv 的路徑。

    注意：
    這個檔案放在 .gitignore 裡，不會推到 GitHub。
    """

    project_root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(project_root, "data", "private_listings_notes.csv")


def import_private_listings():
    """
    將私人整理的看房筆記匯入 listings table。

    使用方式：
    python import_private_listings.py

    注意：
    這個 script 是開發用，
    不是正式產品功能。
    """

    csv_path = get_private_csv_path()

    if not os.path.exists(csv_path):
        print("找不到 private_listings_notes.csv")
        return

    conn = get_db_connection()

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
            conn.execute("""
                INSERT INTO listings (
                    landlord_id,
                    title,
                    area,
                    address,
                    room_type,
                    rent,
                    deposit,
                    size,
                    floor,
                    has_window,
                    can_cook,
                    pet_allowed,
                    water_fee,
                    electricity_fee,
                    internet_included,
                    description,
                    contact_name,
                    contact_phone,
                    image_url,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,
                row.get("title"),
                row.get("area"),
                row.get("address"),
                row.get("room_type"),
                int(row.get("rent") or 0),
                int(row.get("deposit") or 0),
                row.get("size"),
                row.get("floor"),
                int(row.get("has_window") or 0),
                int(row.get("can_cook") or 0),
                int(row.get("pet_allowed") or 0),
                row.get("water_fee"),
                row.get("electricity_fee"),
                int(row.get("internet_included") or 0),
                row.get("description"),
                row.get("contact_name"),
                row.get("contact_phone"),
                row.get("image_url"),
                row.get("status") or "available"
            ))

            count += 1

    conn.commit()
    conn.close()

    print(f"成功匯入 {count} 筆私人房源筆記。")


if __name__ == "__main__":
    import_private_listings()