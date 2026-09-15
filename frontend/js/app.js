const API = "http://127.0.0.1:8000";

let latencyChart;
let availabilityChart;

const els = {
  apiStatus: document.getElementById("apiStatus"),
  serviceSelect: document.getElementById("serviceSelect"),
  summaryGrid: document.getElementById("summaryGrid"),
  serviceGrid: document.getElementById("serviceGrid"),
  incidentTable: document.getElementById("incidentTable"),
  checksTable: document.getElementById("checksTable"),
  message: document.getElementById("message"),
};

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }

  return response.json();
}

function setMessage(text) {
  els.message.textContent = text;
  window.setTimeout(() => {
    if (els.message.textContent === text) {
      els.message.textContent = "";
    }
  }, 5000);
}

function fmtDate(value) {
  if (!value) return "—";
  const normalized = value.endsWith("Z") ? value : value + "Z";
  return new Date(normalized).toLocaleString();
}

function renderSummary(summary) {
  const metrics = [
    ["Online Services", summary.online_services],
    ["Offline Services", summary.offline_services],
    ["Active Incidents", summary.active_incidents],
    ["Average Latency", `${summary.average_latency_ms} ms`],
  ];

  els.summaryGrid.innerHTML = metrics
    .map(([label, value]) => `
      <div class="metric">
        <div class="label">${label}</div>
        <div class="value">${value}</div>
      </div>
    `)
    .join("");
}

function renderServices(services) {
  els.serviceGrid.innerHTML = services
    .map(service => `
      <article class="service-card ${service.status === "OFFLINE" ? "offline" : ""}">
        <div class="state ${service.status.toLowerCase()}">${service.status}</div>
        <h3>${service.name}</h3>
        <div class="service-meta">
          <span>Latency: ${Number(service.latency_ms).toFixed(1)} ms</span>
          <span>Failure streak: ${service.failure_streak}/${service.threshold}</span>
        </div>
      </article>
    `)
    .join("");
}

function renderIncidents(incidents) {
  els.incidentTable.innerHTML = incidents.length
    ? incidents.map(i => `
      <tr>
        <td>${i.incident_number}</td>
        <td>${i.service}</td>
        <td><span class="badge ${i.status.toLowerCase()}">${i.status}</span></td>
        <td>${fmtDate(i.opened_at)}</td>
        <td>${fmtDate(i.resolved_at)}</td>
        <td>${i.duration_seconds == null ? "—" : `${Number(i.duration_seconds).toFixed(1)}s`}</td>
      </tr>
    `).join("")
    : `<tr><td colspan="6">No incidents yet. Simulate a failure and run three checks.</td></tr>`;
}

function renderChecks(checks) {
  els.checksTable.innerHTML = checks.slice(0, 18).map(c => `
    <tr>
      <td>${fmtDate(c.checked_at)}</td>
      <td>${c.service}</td>
      <td><span class="badge ${c.status.toLowerCase()}">${c.status}</span></td>
      <td>${c.http_status}</td>
      <td>${Number(c.latency_ms).toFixed(1)} ms</td>
    </tr>
  `).join("");
}

function renderCharts(data) {
  const chronological = [...data.recent_checks].reverse();
  const labels = chronological.map(c =>
    new Date(c.checked_at + "Z").toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  );
  const latencyValues = chronological.map(c => c.latency_ms);

  if (latencyChart) latencyChart.destroy();
  latencyChart = new Chart(document.getElementById("latencyChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Latency (ms)",
        data: latencyValues,
        tension: .25,
        borderWidth: 2,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true } },
    },
  });

  if (availabilityChart) availabilityChart.destroy();
  availabilityChart = new Chart(document.getElementById("availabilityChart"), {
    type: "doughnut",
    data: {
      labels: ["Online", "Offline"],
      datasets: [{
        data: [
          data.summary.online_services,
          data.summary.offline_services,
        ],
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}

async function populateServices() {
  const services = await api("/api/services");
  els.serviceSelect.innerHTML = services
    .map(s => `<option value="${s.slug}">${s.name}</option>`)
    .join("");
}

async function refresh() {
  try {
    const data = await api("/api/dashboard");
    els.apiStatus.textContent = "API connected";
    renderSummary(data.summary);
    renderServices(data.services);
    renderIncidents(data.incidents);
    renderChecks(data.recent_checks);
    renderCharts(data);
  } catch (error) {
    els.apiStatus.textContent = "API unavailable";
    setMessage(`${error.message}. Start the FastAPI backend on port 8000.`);
  }
}

document.getElementById("failureBtn").addEventListener("click", async () => {
  try {
    const result = await api(
      `/api/services/${els.serviceSelect.value}/simulate-failure`,
      { method: "POST" }
    );
    setMessage(`${result.message} Run three checks to trigger an incident.`);
    await refresh();
  } catch (error) {
    setMessage(error.message);
  }
});

document.getElementById("checkBtn").addEventListener("click", async () => {
  try {
    await api("/api/monitor/run-check", { method: "POST" });
    setMessage("Monitoring cycle completed.");
    await refresh();
  } catch (error) {
    setMessage(error.message);
  }
});

document.getElementById("restoreBtn").addEventListener("click", async () => {
  try {
    const result = await api(
      `/api/services/${els.serviceSelect.value}/restore`,
      { method: "POST" }
    );
    setMessage(result.message + " Any active incident for this service is now resolved.");
    await refresh();
  } catch (error) {
    setMessage(error.message);
  }
});

document.getElementById("resetBtn").addEventListener("click", async () => {
  try {
    const result = await api("/api/reset", { method: "POST" });
    setMessage(result.message);
    await refresh();
  } catch (error) {
    setMessage(error.message);
  }
});

(async function init() {
  try {
    await populateServices();
  } catch (_) {}

  await refresh();
  window.setInterval(refresh, 5000);
})();
