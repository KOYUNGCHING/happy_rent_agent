# Happy Rent Agent

Happy Rent Agent 是一個以中央大學學生租屋情境為核心的 Flask Web App。平台整合房源刊登、房源瀏覽、AI 區域分析、AI 房源分析與看房提醒，協助學生在看房前快速理解「地點、租金、通勤、生活機能與風險」。

## 專案目標

中央大學周邊租屋資訊常散落在社群、地圖、租屋平台與口耳相傳之間。Happy Rent Agent 希望把找房流程集中在同一個介面中，讓學生可以：

- 查看房東上架的中央大學周邊房源
- 用 AI 分析租屋區域是否適合學生生活
- 查看單一房源的租金合理性與看房風險
- 透過聊天助理詢問通勤、租金與看房注意事項
- 讓房東能登入、上架、編輯與下架房源

## 主要功能

### 找房者功能

- 房源列表：查看目前可租房源、租金、地區、房型、設備與描述
- 前端篩選：依關鍵字、房型與最高租金篩選房源
- 房源詳情：查看照片、租金、押金、坪數、樓層、設備、水電與聯絡資訊
- AI 房源分析：分析到校便利性、租金合理性、適合族群、天氣與注意事項
- AI 看房 Checklist：依房源條件產生看房時應詢問的問題

### AI 區域分析

首頁提供區域分析輸入框，可輸入例如「中央大學後門附近」或「中壢車站附近」。後端 Agent 會整合：

- 地點正規化與座標查詢
- 到中央大學距離與通勤時間估算
- 學生生活機能評分
- 租金區間估算
- 天氣資訊
- 空氣品質資訊
- AI 或規則式摘要

### 房東功能

- 註冊 / 登入
- 房東後台
- 新增房源
- 編輯自己上架的房源
- 下架房源，保留歷史資料

## 技術架構

```text
happy_rent_agent/
├── app.py                         # Flask routes 與 API
├── agent_service.py               # AI Agent orchestration
├── database.py                    # SQLite 連線、schema 與 sample data
├── init_db.py                     # 初始化資料庫
├── import_private_listings.py     # 匯入私有房源資料
├── requirements.txt               # Python dependencies
├── data/
│   ├── ncu_rental_estimates.csv   # 中央大學生活圈租金估算
│   ├── real.csv                   # 房源資料
│   └── taiwan_aqi_sample.csv      # AQI sample data
├── templates/                     # Jinja2 pages
├── static/
│   ├── css/style.css              # 全站樣式
│   └── js/                        # 前端互動
└── tools/                         # Agent tools
```

## Agent Tools

`agent_service.py` 串接多個工具模組：

- `geocode_tool.py`：地點與座標查詢
- `ncu_area_tool.py`：中央大學常見生活圈名稱正規化
- `commute_tool.py`：估算到中央大學的距離與通勤時間
- `facility_tool.py`：學生生活機能評分
- `rental_tool.py`：租金區間與負擔判斷
- `weather_tool.py`：天氣資料
- `air_quality_tool.py`：空氣品質資料
- `checklist_tool.py`：看房提醒問題
- `gemini_summary_tool.py`：可選的 Gemini 摘要生成

## 安裝與啟動

### 1. 建立虛擬環境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. 安裝套件

```bash
pip install -r requirements.txt
```

### 3. 設定環境變數

若要啟用 Gemini 摘要，可在專案根目錄建立 `.env`：

```bash
GEMINI_API_KEY=your_api_key_here
```

沒有設定 Gemini API key 時，系統仍會使用 rule-based fallback 摘要。

### 4. 初始化資料庫

```bash
python init_db.py
```

這會建立 `happy_rent.db`，並加入幾筆範例房源。

### 5. 啟動 Flask App

```bash
flask --app app run --debug
```

開啟瀏覽器進入：

```text
http://127.0.0.1:5000
```

## 預設測試資料

初始化後會建立範例房東與房源。

```text
Email: landlord@example.com
Password: 123456
Role: landlord
```

注意：目前 sample user 的密碼在 seed data 中是純文字，正式登入驗證使用的是 hash。若要用登入流程測試房東帳號，建議直接透過註冊頁建立新房東帳號。

## 主要頁面

- `/`：首頁、AI 區域分析、聊天助理
- `/listings`：房源列表
- `/listings/<id>`：房源詳細頁與 AI 房源分析
- `/register`：使用者註冊
- `/login`：使用者登入
- `/logout`：登出
- `/landlord/new`：房東新增房源
- `/landlord/dashboard`：房東後台
- `/landlord/listings/<id>/edit`：編輯房源

## API

### POST `/api/analyze`

分析中央大學周邊租屋區域。

Request:

```json
{
  "query": "中央大學後門附近"
}
```

Response 會包含地點、通勤、生活機能、租金、天氣、空氣品質與 AI 摘要等資料。

### POST `/api/chat`

依目前分析結果回答找房問題。

Request:

```json
{
  "message": "沒有機車方便嗎？",
  "current_area_data": {}
}
```

## 資料庫設計

### `users`

- `id`
- `name`
- `email`
- `password`
- `role`
- `created_at`

### `listings`

- `id`
- `landlord_id`
- `title`
- `area`
- `address`
- `room_type`
- `rent`
- `deposit`
- `size`
- `floor`
- `has_window`
- `can_cook`
- `pet_allowed`
- `water_fee`
- `electricity_fee`
- `internet_included`
- `description`
- `contact_name`
- `contact_phone`
- `image_url`
- `status`
- `created_at`

## 目前限制

- 租金資料為 MVP 估算，不是即時租屋平台價格
- 通勤時間以距離估算，尚未串接真實路線 API
- 圖片目前使用 URL，尚未支援上傳檔案
- 使用 Flask session 與 SQLite，適合教學、展示與 MVP，不建議直接作為正式生產環境
- `app.secret_key` 目前寫在程式中，正式部署應改用環境變數

## 後續可擴充方向

- 串接真實地圖與路線 API
- 上傳房源圖片並建立圖片管理
- 更完整的房源搜尋、排序與收藏
- 房東與學生雙方訊息系統
- 租約、押金、水電規則提醒
- 管理員後台與房源審核
- 部署至 Render、Railway、Fly.io 或其他雲端平台

## 開發指令速查

```bash
# 啟動虛擬環境
source venv/bin/activate

# 安裝 dependencies
pip install -r requirements.txt

# 初始化資料庫
python init_db.py

# 啟動開發伺服器
flask --app app run --debug
```
