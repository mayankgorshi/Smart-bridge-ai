document.addEventListener("DOMContentLoaded", () => {
    initializeBridgeSearch();
    initializeDashboard();
});


function initializeBridgeSearch() {
    const searchInput = document.getElementById("bridgeSearch");
    const bridgeGrid = document.getElementById("bridgeGrid");

    if (!searchInput || !bridgeGrid) {
        return;
    }

    const bridgeCards = Array.from(bridgeGrid.querySelectorAll(".bridge-card"));
    const visibleCount = document.getElementById("visibleCount");
    const emptyState = document.getElementById("emptySearchState");

    const updateVisibility = () => {
        const query = searchInput.value.trim().toLowerCase();
        let matches = 0;

        bridgeCards.forEach((card) => {
            const searchableText = card.dataset.search.toLowerCase();
            const isVisible = searchableText.includes(query);
            card.classList.toggle("hidden", !isVisible);
            if (isVisible) {
                matches += 1;
            }
        });

        visibleCount.textContent = String(matches);
        emptyState.classList.toggle("hidden", matches !== 0);
    };

    searchInput.addEventListener("input", updateVisibility);
}


function initializeDashboard() {
    const dashboard = document.getElementById("dashboardApp");

    if (!dashboard) {
        return;
    }

    const predictionForm = document.getElementById("predictionForm");
    const generateButton = document.getElementById("generateSensorData");
    const formError = document.getElementById("formError");
    const lastGeneratedText = document.getElementById("lastGeneratedText");
    const lastScanTime = document.getElementById("lastScanTime");

    const inputFields = {
        load: document.getElementById("load"),
        vibration: document.getElementById("vibration"),
        cracks: document.getElementById("cracks"),
        stress: document.getElementById("stress"),
    };

    const bridgeAge = Number(dashboard.dataset.age || 0);
    const trafficLevel = dashboard.dataset.trafficLevel || "Medium";
    const bridgeId = dashboard.dataset.bridgeId;

    generateButton.addEventListener("click", () => {
        const sensorData = generateSensorPacket(bridgeAge, trafficLevel);
        inputFields.load.value = sensorData.load;
        inputFields.vibration.value = sensorData.vibration;
        inputFields.cracks.value = sensorData.cracks;
        inputFields.stress.value = sensorData.stress;

        const timestamp = getTimestamp();
        lastGeneratedText.textContent = `Live sensor packet generated at ${timestamp}`;
        lastScanTime.textContent = `Latest telemetry simulation completed at ${timestamp}.`;
        updateSystemStatus("Telemetry Ready", "Fresh sensor values generated and ready for AI inference.");
        hideError(formError);
    });

    predictionForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        hideError(formError);

        const payload = {
            bridge_id: bridgeId,
            load: inputFields.load.value,
            vibration: inputFields.vibration.value,
            cracks: inputFields.cracks.value,
            stress: inputFields.stress.value,
        };

        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || "Prediction failed. Please try again.");
            }

            renderPredictionResult(result);
            updateSystemStatus(result.system_status, result.status_text);
            lastScanTime.textContent = `AI analysis completed at ${getTimestamp()}.`;
        } catch (error) {
            showError(formError, error.message);
        }
    });
}


function generateSensorPacket(age, trafficLevel) {
    const trafficFactorMap = {
        Low: 0.82,
        Medium: 1.0,
        High: 1.18,
        "Very High": 1.34,
        Extreme: 1.5,
    };

    const trafficFactor = trafficFactorMap[trafficLevel] || 1;
    const ageFactor = clamp(0.75 + age / 90, 0.85, 1.7);

    const load = clamp(randomRange(28, 78) * trafficFactor + age * 0.14, 18, 180);
    const vibration = clamp(
        randomRange(0.9, 3.6) * trafficFactor + age * 0.03,
        0.4,
        12.5
    );
    const cracks = clamp(
        randomRange(0.15, 1.8) * ageFactor + (trafficFactor - 1) * 1.8,
        0,
        9.8
    );
    const stress = clamp(
        load * 0.48 + vibration * 4.6 + cracks * 3.8 + age * 0.19 + randomRange(-6, 8),
        20,
        100
    );

    return {
        load: load.toFixed(2),
        vibration: vibration.toFixed(2),
        cracks: cracks.toFixed(2),
        stress: stress.toFixed(2),
    };
}


function renderPredictionResult(result) {
    const predictionBadge = document.getElementById("predictionBadge");
    const resultCore = document.getElementById("resultCore");
    const resultIcon = document.getElementById("resultIcon");
    const predictionText = document.getElementById("predictionText");
    const predictionDescription = document.getElementById("predictionDescription");
    const confidenceValue = document.getElementById("confidenceValue");
    const riskMeterValue = document.getElementById("riskMeterValue");
    const riskMeterFill = document.getElementById("riskMeterFill");
    const recommendedAction = document.getElementById("recommendedAction");
    const sensorSnapshotList = document.getElementById("sensorSnapshotList");
    const resultSystemStatus = document.getElementById("resultSystemStatus");
    const conditionText = document.getElementById("conditionText");

    const stateClass = result.badge_class;
    const stateLabel = result.prediction;
    const stateClasses = ["safe", "warning", "critical", "neutral"];

    predictionBadge.classList.remove(...stateClasses);
    resultCore.classList.remove(...stateClasses);
    riskMeterFill.classList.remove(...stateClasses);

    predictionBadge.classList.add(stateClass);
    resultCore.classList.add(stateClass);
    riskMeterFill.classList.add(stateClass);

    predictionBadge.textContent = stateLabel;
    resultIcon.innerHTML = result.icon;
    predictionText.textContent = stateLabel;
    predictionDescription.textContent = result.status_text;
    confidenceValue.textContent = `${result.confidence}%`;
    riskMeterValue.textContent = `${result.risk_meter}%`;
    riskMeterFill.style.width = `${result.risk_meter}%`;
    recommendedAction.textContent = result.recommended_action;
    resultSystemStatus.textContent = result.system_status;
    conditionText.textContent = result.estimated_condition;

    sensorSnapshotList.innerHTML = Object.entries(result.sensor_snapshot)
        .map(([label, value]) => `<li>${label}: ${value}</li>`)
        .join("");
}


function updateSystemStatus(title, subtitle) {
    const statusTitle = document.getElementById("systemStatusText");
    const statusSubtitle = document.getElementById("systemStatusSubtext");

    if (!statusTitle || !statusSubtitle) {
        return;
    }

    statusTitle.textContent = title;
    statusSubtitle.textContent = subtitle;
}


function showError(target, message) {
    target.textContent = message;
    target.classList.remove("hidden");
}


function hideError(target) {
    target.textContent = "";
    target.classList.add("hidden");
}


function randomRange(minimum, maximum) {
    return Math.random() * (maximum - minimum) + minimum;
}


function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
}


function getTimestamp() {
    return new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}
