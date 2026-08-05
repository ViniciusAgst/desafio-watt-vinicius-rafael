const WINDOW_MS = 20000;
const POLL_MS = 100;

const DEVICES = {
  grid: {
    color: "#4dd0e1",
    metric: v => v.grid.voltage,
    endpoint: "grid",
    yMin: 0,
    yMax: 400
  },
  compressor: {
    color: "#ffb74d",
    metric: v => v.compressor.current,
    endpoint: "compressor",
    yMin: 0,
    yMax: 500
  },
  extruder: {
    color: "#ba68c8",
    metric: v => v.extruder.current_thd,
    endpoint: "extruder",
    yMin: 0,
    yMax: 100
  }
};

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function buildChart(canvasId, color, yMin, yMax) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const gradient = ctx.createLinearGradient(0, 0, 0, 160);
  gradient.addColorStop(0, hexToRgba(color, 0.35));
  gradient.addColorStop(1, hexToRgba(color, 0.0));

  return new Chart(ctx, {
    type: "line",
    data: {
      datasets: [{
        data: [],
        borderColor: color,
        backgroundColor: gradient,
        borderWidth: 2.5,
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        cubicInterpolationMode: "monotone"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400, easing: "easeOutQuart" },
      animations: {
        x: { duration: 0 }
      },
      transitions: {
        active: { animation: { duration: 0 } }
      },
      interaction: { intersect: false },
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: {
          type: "linear",
          min: Date.now() - WINDOW_MS,
          max: Date.now(),
          ticks: {
            color: "#8a94ab",
            maxTicksLimit: 5
          },
            grid: { color: "rgba(255,255,255,0.05)" }
        },
        y: {
          min: yMin,
          max: yMax,
          ticks: { color: "#8a94ab" },
          grid: { color: "rgba(255,255,255,0.05)" }
        }
      }
    }
  });
}

const charts = {
  grid: buildChart("chart-grid", DEVICES.grid.color, DEVICES.grid.yMin, DEVICES.grid.yMax),
  compressor: buildChart("chart-compressor", DEVICES.compressor.color, DEVICES.compressor.yMin, DEVICES.compressor.yMax),
  extruder: buildChart("chart-extruder", DEVICES.extruder.color, DEVICES.extruder.yMin, DEVICES.extruder.yMax)
};

function pushPoint(key, value) {
  const chart = charts[key];
  const now = Date.now();
  const data = chart.data.datasets[0].data;

  data.push({ x: now, y: value });

  const cutoff = now - WINDOW_MS;
  while (data.length && data[0].x < cutoff) {
    data.shift();
  }

  chart.options.scales.x.min = cutoff;
  chart.options.scales.x.max = now;
  chart.update("none");

  document.getElementById(`value-${key}`).textContent = value.toFixed(1);
}

async function poll() {
  try {
    const res = await fetch("/data");
    if (!res.ok) return;
    const json = await res.json();

    for (const key in DEVICES) {
      const value = DEVICES[key].metric(json);
      pushPoint(key, value);
    }
  } catch (err) {
    console.error("Falha ao buscar /data:", err);
  }
}

function setFaultState(key, active) {
  const card = document.getElementById(`card-${key}`);
  const status = document.getElementById(`status-${key}`);
  const startBtn = document.getElementById(`start-${key}`);
  const stopBtn = document.getElementById(`stop-${key}`);

  if (active) {
    status.textContent = "Em Falha";
    status.classList.add("faulted");
    card.classList.add("pulse");
    startBtn.disabled = true;
    stopBtn.disabled = false;
  } else {
    status.textContent = "Normal";
    status.classList.remove("faulted");
    card.classList.remove("pulse");
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
}

async function callAction(endpoint, action) {
  try {
    const res = await fetch(`/${endpoint}/${action}`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return true;
  } catch (err) {
    console.error(`Falha ao chamar /${endpoint}/${action}:`, err);
    return false;
  }
}

for (const key in DEVICES) {
  const endpoint = DEVICES[key].endpoint;

  document.getElementById(`start-${key}`).addEventListener("click", async () => {
    const ok = await callAction(endpoint, "start");
    if (ok) setFaultState(key, true);
  });

  document.getElementById(`stop-${key}`).addEventListener("click", async () => {
    const ok = await callAction(endpoint, "stop");
    if (ok) setFaultState(key, false);
  });
}

poll();
setInterval(poll, POLL_MS);