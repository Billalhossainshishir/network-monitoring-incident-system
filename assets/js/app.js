const FAILURE_THRESHOLD = 3;

const serviceSeed = [
  { slug: "web", name: "Web Server", description: "Public-facing website service" },
  { slug: "api", name: "API Server", description: "Core application API service" },
  { slug: "database", name: "Database Service", description: "Primary application database" },
  { slug: "auth", name: "Authentication Service", description: "Identity and login service" },
  { slug: "file", name: "File Service", description: "Document and file storage service" },
];

let services = [];
let checks = [];
let incidents = [];
let incidentCounter = 1;
let latencyChart;
let availabilityChart;
let autoTimer;

const els = {
  serviceSelect: document.getElementById("serviceSelect"),
  summaryGrid: document.getElementById("summaryGrid"),
  serviceGrid: document.getElementById("serviceGrid"),
  incidentTable: document.getElementById("incidentTable"),
  checksTable: document.getElementById("checksTable"),
  message: document.getElementById("message"),
};

function nowIso() {
  return new Date().toISOString();
}

function resetState() {
  services = serviceSeed.map(s => ({
    ...s,
    forcedOffline: false,
    failureStreak: 0,
    status: "ONLINE",
    latencyMs: randomLatency(true),
  }));
  checks = [];
  incidents = [];
  incidentCounter = 1;

  for (let i = 0; i < 8; i += 1) {
    services.forEach(service => recordCheck(service, true, true));
  }

  render();
}

function randomLatency(online) {
  return online
    ? Number((22 + Math.random() * 105).toFixed(1))
    : Number((850 + Math.random() * 900).toFixed(1));
}

function incidentId() {
  const year = new Date().getFullYear();
  return `INC-${year}-${String(incidentCounter++).padStart(4, "0")}`;
}

function activeIncidentFor(slug) {
  return incidents.find(i => i.serviceSlug === slug && i.status === "ACTIVE");
}

function recordCheck(service, onlineOverride = null, seedMode = false) {
  const online = onlineOverride ?? !service.forcedOffline;
  const latency = randomLatency(online);

  if (online) {
    service.status = "ONLINE";
    service.latencyMs = latency;
    service.failureStreak = 0;

    const active = activeIncidentFor(service.slug);
    if (active && !seedMode) {
      active.status = "RESOLVED";
      active.resolvedAt = nowIso();
      active.durationSeconds = Math.max(
        1,
        Math.round((new Date(active.resolvedAt) - new Date(active.openedAt)) / 1000)
      );
    }
  } else {
    service.status = "OFFLINE";
    service.latencyMs = latency;
    service.failureStreak += 1;

    if (service.failureStreak >= FAILURE_THRESHOLD && !activeIncidentFor(service.slug)) {
      incidents.unshift({
        id: incidentId(),
        serviceSlug: service.slug,
        serviceName: service.name,
        status: "ACTIVE",
        openedAt: nowIso(),
        resolvedAt: null,
        durationSeconds: null,
        reason: `${FAILURE_THRESHOLD} consecutive health-check failures detected`,
      });
    }
  }

  checks.unshift({
    time: nowIso(),
    serviceSlug: service.slug,
    serviceName: service.name,
    status: online ? "ONLINE" : "OFFLINE",
    httpStatus: online ? 200 : 503,
    latencyMs: latency,
  });

  checks = checks.slice(0, 80);
}

function runCycle() {
  services.forEach(service => recordCheck(service));
  render();
}

function simulateFailure() {
  const service = services.find(s => s.slug === els.serviceSelect.value);
  service.forcedOffline = true;
  service.failureStreak = 0;
  showMessage(`${service.name} is now simulating an outage. Run three health checks to trigger an incident.`);
  render();
}

function restoreService() {
  const service = services.find(s => s.slug === els.serviceSelect.value);
  service.forcedOffline = false;
  recordCheck(service, true);
  showMessage(`${service.name} recovered. Any active incident for this service was resolved automatically.`);
  render();
}

function showMessage(text) {
  els.message.textContent = text;
  clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(() => {
    if (els.message.textContent === text) els.message.textContent = "";
  }, 6000);
}

function calculateSummary() {
  const online = services.filter(s => s.status === "ONLINE").length;
  const activeIncidents = incidents.filter(i => i.status === "ACTIVE").length;
  const recentOnlineChecks = checks.filter(c => c.status === "ONLINE").slice(0, 25);
  const avgLatency = recentOnlineChecks.length
    ? recentOnlineChecks.reduce((sum, c) => sum + c.latencyMs, 0) / recentOnlineChecks.length
    : 0;

  return {
    online,
    offline: services.length - online,
    activeIncidents,
    avgLatency: Number(avgLatency.toFixed(1)),
  };
}

function renderSummary() {
  const summary = calculateSummary();
  const cards = [
    ["Online Services", summary.online],
    ["Offline Services", summary.offline],
    ["Active Incidents", summary.activeIncidents],
    ["Average Latency", `${summary.avgLatency} ms`],
  ];

  els.summaryGrid.innerHTML = cards.map(([label, value]) => `
    <article class="metric">
      <div class="metric-label">${label}</div>
      <div class="metric-value">${value}</div>
    </article>
  `).join("");
}

function renderServices() {
  els.serviceGrid.innerHTML = services.map(service => `
    <article class="service-card ${service.status === "OFFLINE" ? "offline" : ""}">
      <span class="state ${service.status.toLowerCase()}">${service.status}</span>
      <h3>${service.name}</h3>
      <div class="service-meta">
        <span>${service.description}</span>
        <span>Latency: ${service.latencyMs.toFixed(1)} ms</span>
        <span>Failure streak: ${service.failureStreak}/${FAILURE_THRESHOLD}</span>
      </div>
    </article>
  `).join("");
}

function formatTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function renderIncidents() {
  els.incidentTable.innerHTML = incidents.length
    ? incidents.map(incident => `
      <tr>
        <td>${incident.id}</td>
        <td>${incident.serviceName}</td>
        <td><span class="badge ${incident.status.toLowerCase()}">${incident.status}</span></td>
        <td>${formatTime(incident.openedAt)}</td>
        <td>${formatTime(incident.resolvedAt)}</td>
        <td>${incident.durationSeconds == null ? "—" : `${incident.durationSeconds}s`}</td>
      </tr>
    `).join("")
    : `<tr><td colspan="6">No incidents yet. Simulate a failure and run three health checks.</td></tr>`;
}

function renderChecks() {
  els.checksTable.innerHTML = checks.slice(0, 18).map(check => `
    <tr>
      <td>${new Date(check.time).toLocaleTimeString()}</td>
      <td>${check.serviceName}</td>
      <td><span class="badge ${check.status.toLowerCase()}">${check.status}</span></td>
      <td>${check.httpStatus}</td>
      <td>${check.latencyMs.toFixed(1)} ms</td>
    </tr>
  `).join("");
}

function renderCharts() {
  const recent = [...checks].slice(0, 30).reverse();
  const labels = recent.map(c => new Date(c.time).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }));

  if (latencyChart) latencyChart.destroy();
  latencyChart = new Chart(document.getElementById("latencyChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Latency (ms)",
        data: recent.map(c => c.latencyMs),
        tension: .28,
        borderWidth: 2,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#cfe1f1" } } },
      scales: {
        x: { ticks: { color: "#829ab3" }, grid: { color: "rgba(62, 88, 116, .25)" } },
        y: { beginAtZero: true, ticks: { color: "#829ab3" }, grid: { color: "rgba(62, 88, 116, .25)" } },
      },
    },
  });

  const summary = calculateSummary();
  if (availabilityChart) availabilityChart.destroy();
  availabilityChart = new Chart(document.getElementById("availabilityChart"), {
    type: "doughnut",
    data: {
      labels: ["Online", "Offline"],
      datasets: [{ data: [summary.online, summary.offline] }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#cfe1f1" } } },
    },
  });
}

function render() {
  renderSummary();
  renderServices();
  renderIncidents();
  renderChecks();
  renderCharts();
}

function initSelect() {
  els.serviceSelect.innerHTML = serviceSeed
    .map(s => `<option value="${s.slug}">${s.name}</option>`)
    .join("");
}

document.getElementById("failureBtn").addEventListener("click", simulateFailure);
document.getElementById("checkBtn").addEventListener("click", () => {
  runCycle();
  showMessage("Monitoring cycle completed.");
});
document.getElementById("restoreBtn").addEventListener("click", restoreService);
document.getElementById("resetBtn").addEventListener("click", () => {
  resetState();
  showMessage("Demo reset. All services are online and incident history is clear.");
});

initSelect();
resetState();

autoTimer = window.setInterval(() => {
  runCycle();
}, 7000);
