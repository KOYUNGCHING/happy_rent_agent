function filterListings() {
    /*
      前端簡易篩選功能。

      目前這是 MVP 版本：
      - 不重新呼叫後端
      - 直接在目前頁面上篩選已載入的房源卡片

      好處：
      - 寫法簡單
      - 不需要新增 API
      - 適合第一版展示

      未來如果資料很多，可以改成：
      GET /listings?keyword=後門&room_type=獨立套房&max_rent=8000
      讓後端 SQL 直接篩選。
    */

    // 取得使用者輸入的關鍵字
    const keyword = document.getElementById("keywordInput").value.trim();

    // 取得房型篩選條件
    const roomType = document.getElementById("roomTypeFilter").value;

    // 取得最高租金
    const maxRentValue = document.getElementById("maxRentFilter").value;

    // 如果使用者沒有輸入最高租金，就設成 Infinity，代表不限制
    const maxRent = maxRentValue ? Number(maxRentValue) : Infinity;

    // 取得所有房源卡片
    const cards = document.querySelectorAll(".listing-card");

    cards.forEach(card => {
        /*
          每一張 card 上面都有 data-* 屬性：
          data-title
          data-area
          data-room-type
          data-rent

          這些是從 listings.html 裡由 Flask/Jinja2 產生的。
        */

        const title = card.dataset.title || "";
        const area = card.dataset.area || "";
        const cardRoomType = card.dataset.roomType || "";
        const rent = Number(card.dataset.rent || 0);

        // 判斷關鍵字是否符合
        // 使用者輸入空字串時，代表不篩選關鍵字
        const matchKeyword =
            !keyword ||
            title.includes(keyword) ||
            area.includes(keyword) ||
            cardRoomType.includes(keyword);

        // 判斷房型是否符合
        const matchRoomType =
            !roomType || cardRoomType === roomType;

        // 判斷租金是否符合
        const matchRent = rent <= maxRent;

        // 三個條件都符合才顯示
        if (matchKeyword && matchRoomType && matchRent) {
            card.style.display = "flex";
        } else {
            card.style.display = "none";
        }
    });
}


// 讓使用者在篩選欄位按 Enter 時也可以觸發篩選
document.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        const activeElement = document.activeElement;

        if (
            activeElement.id === "keywordInput" ||
            activeElement.id === "maxRentFilter"
        ) {
            filterListings();
        }
    }
});
