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

    document.getElementById("transportScore").textContent =
        `${data.transport.transport_score} / 100`;
    document.getElementById("transportSummary").textContent =
        data.transport.summary;

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

    document.getElementById("weatherInfo").textContent =
        `${data.weather.weather}，溫度 ${data.weather.temperature}，降雨機率 ${data.weather.rain_probability}。${data.weather.summary}`;

    document.getElementById("rentalInfo").textContent =
        `套房估計：${data.rental.studio_range}；雅房估計：${data.rental.shared_room_range}。${data.rental.summary}`;

    renderList("prosList", data.ai_analysis.pros);
    renderList("consList", data.ai_analysis.cons);
    renderList("suitableList", data.ai_analysis.suitable_for);

    document.getElementById("suggestion").textContent =
        data.ai_analysis.suggestion;
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