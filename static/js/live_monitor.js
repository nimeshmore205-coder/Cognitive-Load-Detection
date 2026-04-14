// =======================================
// Live Cognitive Load Monitor (Enterprise)
// =======================================

// ---------- CONFIG ----------
const POLL_INTERVAL = 1000;      // 1 sec
const MAX_POINTS = 30;           // chart points
const ALERT_COOLDOWN = 15;       // seconds

let lastAlertTime = 0;
let alertTriggered = false;

// ---------- CHART SETUP ----------
const ctx = document.getElementById("fatigueChart").getContext("2d");

const fatigueChart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            {
                label: "EAR",
                data: [],
                borderColor: "red",
                tension: 0.3,
                fill: false
            },
            {
                label: "Blink Rate",
                data: [],
                borderColor: "blue",
                tension: 0.3,
                fill: false
            }
        ]
    },
    options: {
        responsive: true,
        animation: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

// ---------- MAIN LOOP ----------
function updateMetrics() {
    fetch("/live/metrics")
        .then(res => res.json())
        .then(data => {

            // --------- Update text UI ---------
            setText("ear", data.ear);
            setText("blink_rate", data.blink_rate);
            setText("rule", data.rule);
            setText("rf", data.rf);
            setText("lstm", data.lstm);

            // --------- Update chart ---------
            const time = new Date().toLocaleTimeString();

            fatigueChart.data.labels.push(time);
            fatigueChart.data.datasets[0].data.push(data.ear);
            fatigueChart.data.datasets[1].data.push(data.blink_rate);

            if (fatigueChart.data.labels.length > MAX_POINTS) {
                fatigueChart.data.labels.shift();
                fatigueChart.data.datasets.forEach(ds => ds.data.shift());
            }

            fatigueChart.update();

            // --------- Fatigue detection ---------
            const isHigh =
                data.rule === "High" ||
                data.rf === "High" ||
                data.lstm === "High";

            handleFatigueAlert(isHigh);
        })
        .catch(err => console.error("Metrics fetch error:", err));
}

// ---------- ALERT LOGIC ----------
function handleFatigueAlert(isHigh) {
    const now = Date.now() / 1000;

    if (isHigh) {
        if (!alertTriggered && (now - lastAlertTime) > ALERT_COOLDOWN) {
            triggerAlert();
            alertTriggered = true;
            lastAlertTime = now;
        }
    } else {
        alertTriggered = false;
        hideAlert();
    }
}

function triggerAlert() {
    console.warn("⚠ High Cognitive Load Detected");

    showAlert();
    playSound();

    // Notify backend (MySQL logging)
    fetch("/live/alert", { method: "POST" })
        .catch(err => console.error("Alert logging failed:", err));
}

// ---------- UI HELPERS ----------
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.innerText = value ?? "-";
}

function showAlert() {
    const box = document.getElementById("fatigueAlert");
    if (box) box.classList.remove("d-none");
}

function hideAlert() {
    const box = document.getElementById("fatigueAlert");
    if (box) box.classList.add("d-none");
}

function playSound() {
    const audio = document.getElementById("alertSound");
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(() => {
            console.warn("Audio blocked by browser");
        });
    }
}

// ---------- START ----------
setInterval(updateMetrics, POLL_INTERVAL);
