let currentAreaData = null;

async function analyzeArea() {
    const input = document.getElementById("locationInput").value.trim();

    if (!input) {
        alert("請先輸入想分析的地點！");
        return;
    }

    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("resultSection").classList.add("hidden");

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: input })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "分析失敗");
        }

        currentAreaData = data;
        renderResult(data);
        addBotMessage(`我已經完成 ${data.location.location_name} 的租屋地區分析，你可以繼續問我這個地區適不適合你。`);

    } catch (error) {
        alert(error.message);
    } finally {
        document.getElementById("loading").classList.add("hidden");
    }
}

function renderResult(data) {
    document.getElementById("resultSection").classList.remove("hidden");

    document.getElementById("resultTitle").textContent =
        `${data.location.location_name} 租屋地區分析`;

    // 顯示到校便利性分數
    // commute_score 是後端 Commute Tool 根據距離中央大學的遠近計算出來的
    document.getElementById("commuteScore").textContent =
        `${data.commute.commute_score} / 100`;

    // 顯示到中央大學的距離與估算通勤時間
    document.getElementById("commuteSummary").textContent =
        data.commute.summary;
    document.getElementById("facilityScore").textContent =
        `${data.facilities.facility_score} / 100`;
    document.getElementById("facilitySummary").textContent =
        data.facilities.summary;

    document.getElementById("rentalLevel").textContent =
        data.rental.rental_level;
    document.getElementById("rentalSummary").textContent =
        data.rental.summary;

    document.getElementById("airQuality").textContent =
        `${data.air_quality.level} / AQI ${data.air_quality.aqi}`;
    document.getElementById("airSummary").textContent =
        data.air_quality.summary;

    document.getElementById("aiSummary").textContent =
        data.ai_analysis.summary;
    document.getElementById("coordinateText").textContent =
        `座標：${data.location.latitude}, ${data.location.longitude}`;
    // 顯示天氣資訊
    // 這裡使用後端 Weather Tool 回傳的真實資料
    // precipitation 是降雨量，不是降雨機率，所以文字要寫成「降雨量」
    document.getElementById("weatherInfo").textContent =
        `${data.weather.weather}，溫度 ${data.weather.temperature}，` +
        `濕度 ${data.weather.humidity}，降雨量 ${data.weather.precipitation}，` +
        `風速 ${data.weather.wind_speed}。${data.weather.summary}`;
    document.getElementById("rentalInfo").textContent =
        `套房估計：${data.rental.studio_range}；雅房估計：${data.rental.shared_room_range}。${data.rental.summary}`;

    renderList("prosList", data.ai_analysis.pros);
    renderList("consList", data.ai_analysis.cons);
    renderList("suitableList", data.ai_analysis.suitable_for);

    document.getElementById("suggestion").textContent =
        data.ai_analysis.suggestion;

    // 顯示到中央大學的不同通勤方式估算
    document.getElementById("commuteInfo").textContent =
        `距離中央大學約 ${data.commute.distance_km} 公里。` +
        `估計步行約 ${data.commute.walking_minutes} 分鐘，` +
        `騎腳踏車約 ${data.commute.bike_minutes} 分鐘，` +
        `騎機車約 ${data.commute.scooter_minutes} 分鐘。`;
}

function renderList(elementId, items) {
    const list = document.getElementById(elementId);
    list.innerHTML = "";

    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        list.appendChild(li);
    });
}

async function sendChat() {
    const input = document.getElementById("chatInput");
    const message = input.value.trim();

    if (!message) {
        return;
    }

    addUserMessage(message);
    input.value = "";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                current_area_data: currentAreaData
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "回覆失敗");
        }

        addBotMessage(data.reply);

    } catch (error) {
        addBotMessage("目前聊天功能發生錯誤，請稍後再試。");
    }
}

function addUserMessage(message) {
    const chatMessages = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "user-message";
    div.textContent = message;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addBotMessage(message) {
    const chatMessages = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "bot-message";
    div.textContent = message;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.getElementById("chatInput").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        sendChat();
    }
});

document.getElementById("locationInput").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        analyzeArea();
    }
});