// EcoSort AI - Frontend Dashboard Application with RCA & AI Chatbot

const API_BASE = "";
let ws = null;
let timelineChart = null;
let distributionChart = null;
let currentTab = "overview";
let currentPage = 1;

// Class color mappings (Futuristic Blue & Purple Palette)
const CLASS_COLORS = {
  "plastic_bottle": "#2563EB",
  "plastic_bag": "#06B6D4",
  "paper": "#10B981",
  "cardboard": "#059669",
  "metal_can": "#7C3AED",
  "glass_bottle": "#6366F1"
};

// Macro Category Mappings & Badges
const MACRO_INFO = {
  "Anorganik": { color: "#2563EB", bg: "rgba(37, 99, 235, 0.12)", icon: "🧴" },
  "Organik": { color: "#10B981", bg: "rgba(16, 185, 129, 0.12)", icon: "🍃" },
  "Berbahaya": { color: "#7C3AED", bg: "rgba(124, 58, 237, 0.12)", icon: "⚠️" }
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initWebSocket();
  loadDashboardData();
  loadDetections();
  loadNotifications();
  loadReports();
  loadSettings();
  loadRequirementsList();
  loadRCA();

  // Polling for dashboard KPI sync
  setInterval(() => {
    if (currentTab === "overview" || currentTab === "analytics") {
      loadDashboardData();
    }
  }, 4000);
});

// Navigation Handling
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = item.getAttribute('data-tab');
      switchTab(tab);
    });
  });
  // Initialize analytics on load if default tab is analytics
  if (currentTab === 'analytics') loadAnalytics();
}


// Teachable Machine Model Integration
const TM_MODEL_URL = "https://teachablemachine.withgoogle.com/models/UnyiHWtLn/";
let tmModel = null;
let tmWebcam = null;
let tmLabelContainer = null;
let tmMaxPredictions = 0;

async function initTMModel() {
  if (tmModel) return; // already loaded
  const modelURL = TM_MODEL_URL + "model.json";
  const metadataURL = TM_MODEL_URL + "metadata.json";
  tmModel = await tmImage.load(modelURL, metadataURL);
  tmMaxPredictions = tmModel.getTotalClasses();
  // Setup webcam element
  const flip = true;
  tmWebcam = new tmImage.Webcam(200, 200, flip);
  await tmWebcam.setup();
  await tmWebcam.play();
  document.getElementById("tm-webcam-container").appendChild(tmWebcam.canvas);
  tmLabelContainer = document.getElementById("tm-label-container");
  tmLabelContainer.innerHTML = "";
  for (let i = 0; i < tmMaxPredictions; i++) {
    const div = document.createElement("div");
    tmLabelContainer.appendChild(div);
  }
  window.requestAnimationFrame(tmLoop);
}

async function tmLoop() {
  if (!tmWebcam) return;
  tmWebcam.update();
  await tmPredict();
  window.requestAnimationFrame(tmLoop);
}

async function tmPredict() {
  const prediction = await tmModel.predict(tmWebcam.canvas);
  for (let i = 0; i < tmMaxPredictions; i++) {
    const classPrediction = prediction[i].className + ": " + (prediction[i].probability * 100).toFixed(1) + "%";
    tmLabelContainer.childNodes[i].innerHTML = classPrediction;
  }
}

// Hook into tab switch
function switchTab(tabId) {
  // existing code ... (keep unchanged until line 64)

  currentTab = tabId;
  document.querySelectorAll(".nav-item").forEach(el => {
    el.classList.toggle("active", el.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach(el => {
    el.classList.toggle("active", el.id === `tab-${tabId}`);
  });

  const titles = {
    overview: "Dashboard Overview",
    live: "Live Webcam Detection",
    history: "Detection History",
    rca: "Root Cause Analysis (RCA)",
    chatbot: "AI Waste & RCA Assistant",
    analytics: "Detailed Analytics",
    notifications: "Notification Center",
    reports: "PDF Reports",
    settings: "System Settings",
    requirements: "Project Requirements & Specs"
  };
  document.getElementById("page-title").textContent = titles[tabId] || "EcoSort AI";

  if (tabId === "history") loadDetections();
  if (tabId === "rca") loadRCA();
  if (tabId === "notifications") loadNotifications();
  if (tabId === "reports") loadReports();
  if (tabId === "analytics") startAnalyticsPolling();
  else stopAnalyticsPolling();
}

// WebSocket Connection
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/detection`;
  const wsBadge = document.getElementById("badge-ws");

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsBadge.className = "badge badge-success";
      wsBadge.innerHTML = '<span class="badge-dot"></span> WS Connected';
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleLiveUpdate(data);
      } catch (err) {
        console.error("WS Parse error", err);
      }
    };

    ws.onclose = () => {
      wsBadge.className = "badge badge-danger";
      wsBadge.innerHTML = '<span class="badge-dot"></span> WS Disconnected';
      setTimeout(initWebSocket, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  } catch (e) {
    console.error("WS connection failed", e);
  }
}

// Load analytics charts
// ── Analytics: real-time polling ──────────────────────────────────────────
let _analyticsInterval = null;

function startAnalyticsPolling() {
  loadAnalytics();
  if (_analyticsInterval) clearInterval(_analyticsInterval);
  _analyticsInterval = setInterval(() => {
    if (currentTab === 'analytics') loadAnalytics();
  }, 3000);
}

function stopAnalyticsPolling() {
  if (_analyticsInterval) { clearInterval(_analyticsInterval); _analyticsInterval = null; }
}

async function loadAnalytics() {
  try {
    const hours = parseInt(document.getElementById('analytics-hours')?.value || '24');
    const res = await fetch(`${API_BASE}/api/dashboard/charts?hours=${hours}`);
    if (!res.ok) return;
    const data = await res.json();

    const CLASS_COLORS = ['#2563eb','#06b6d4','#10b981','#059669','#7c3aed','#6366f1'];
    const MACRO_COLORS = ['#2563eb','#10b981','#7c3aed'];

    // ── 1. Bar chart: detections per class ──────────────────────────
    const classLabels = (data.distribution?.labels) || [];
    const classValues = (data.distribution?.values) || [];

    const ctxClass = document.getElementById('analytics-chart-class');
    if (ctxClass) {
      if (!window._analyticsClassChart) {
        window._analyticsClassChart = new Chart(ctxClass.getContext('2d'), {
          type: 'bar',
          data: {
            labels: classLabels,
            datasets: [{ label: 'Jumlah Deteksi', data: classValues,
              backgroundColor: CLASS_COLORS.slice(0, classLabels.length),
              borderRadius: 6, borderSkipped: false }]
          },
          options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: '#f1f5f9' } },
              x: { grid: { display: false }, ticks: { font: { size: 11 } } }
            }
          }
        });
      } else {
        // Update in place — no flicker
        window._analyticsClassChart.data.labels = classLabels;
        window._analyticsClassChart.data.datasets[0].data = classValues;
        window._analyticsClassChart.data.datasets[0].backgroundColor = CLASS_COLORS.slice(0, classLabels.length);
        window._analyticsClassChart.update('active');
      }
    }

    // ── 2. Horizontal bar: macro categories ─────────────────────────
    const macroLabels = data.macro_distribution?.labels || ['Anorganik','Organik','Berbahaya'];
    const macroValues = data.macro_distribution?.values || [0,0,0];

    macroLabels.forEach((label, i) => {
      const el = document.getElementById(`analytics-count-${label.toLowerCase()}`);
      if (el) el.textContent = macroValues[i] ?? 0;
    });

    const ctxMacro = document.getElementById('analytics-chart-macro');
    if (ctxMacro) {
      if (!window._analyticsMacroChart) {
        window._analyticsMacroChart = new Chart(ctxMacro.getContext('2d'), {
          type: 'bar',
          data: {
            labels: macroLabels,
            datasets: [{ label: 'Jumlah', data: macroValues,
              backgroundColor: MACRO_COLORS, borderRadius: 8, borderSkipped: false }]
          },
          options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
            plugins: { legend: { display: false } },
            scales: {
              x: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: '#f1f5f9' } },
              y: { grid: { display: false }, ticks: { font: { size: 13, weight: '700' } } }
            }
          }
        });
      } else {
        window._analyticsMacroChart.data.labels = macroLabels;
        window._analyticsMacroChart.data.datasets[0].data = macroValues;
        window._analyticsMacroChart.update('active');
      }
    }

    // ── 3. Line chart: timeline ──────────────────────────────────────
    const timeLabels = data.timeline?.labels || [];
    const timeValues = data.timeline?.values || [];

    const ctxTime = document.getElementById('analytics-chart-timeline');
    if (ctxTime) {
      if (!window._analyticsTimelineChart) {
        window._analyticsTimelineChart = new Chart(ctxTime.getContext('2d'), {
          type: 'line',
          data: {
            labels: timeLabels,
            datasets: [{ label: 'Deteksi per Jam', data: timeValues,
              borderColor: '#4f46e5', backgroundColor: 'rgba(79,70,229,0.08)',
              fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#4f46e5' }]
          },
          options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: '#f1f5f9' } },
              x: { grid: { display: false }, ticks: { maxTicksLimit: 12, font: { size: 11 } } }
            }
          }
        });
      } else {
        window._analyticsTimelineChart.data.labels = timeLabels;
        window._analyticsTimelineChart.data.datasets[0].data = timeValues;
        window._analyticsTimelineChart.update('active');
      }
    }

  } catch (e) {
    console.error('Analytics load error:', e);
  }
}

// Speech synthesis for live detection
function speakDetection(className) {
  const mapping = {
    plastic_bottle: 'Botol plastik',
    plastic_bag: 'Kantong plastik',
    glass_bottle: 'Botol kaca',
    paper: 'Kertas',
    cardboard: 'Kardus',
    metal_can: 'Kaleng logam'
  };
  const text = mapping[className] || className;
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = 'id-ID';
  window.speechSynthesis.speak(utter);
}

// Update live detection handling to include speech
function handleLiveUpdate(data) {
  const fpsEl = document.getElementById('live-fps');
  if (fpsEl) fpsEl.textContent = `${data.fps} FPS`;
  const totalEl = document.getElementById('live-session-total');
  if (totalEl) totalEl.textContent = data.total_count || 0;
  if (data.session_counts) {
    for (const [cname, cnt] of Object.entries(data.session_counts)) {
      const el = document.getElementById(`live-cnt-${cname}`);
      if (el) el.textContent = cnt;
    }
    if (data.latest_class) {
      speakDetection(data.latest_class);
    }
  }
  // existing badge updates ...
  const camBadge = document.getElementById('badge-camera');
  if (data.camera_status === 'running') {
    camBadge.className = 'badge badge-success';
    camBadge.innerHTML = '<span class="badge-dot"></span> Camera Active';
  } else {
    camBadge.className = 'badge badge-warning';
    camBadge.innerHTML = '<span class="badge-dot"></span> Camera Idle';
  }
  const modelBadge = document.getElementById('badge-model');
  if (data.model_status === 'ready') {
    modelBadge.className = 'badge badge-success';
    modelBadge.innerHTML = '<span class="badge-dot"></span> Model Ready';
  } else if (data.model_status === 'demo') {
    modelBadge.className = 'badge badge-info';
    modelBadge.innerHTML = '<span class="badge-dot"></span> Demo Detector';
  } else {
    modelBadge.className = 'badge badge-purple';
    modelBadge.innerHTML = '<span class="badge-dot"></span> Model Training...';
  }
}

function handleLiveUpdate(data) {
  const fpsEl = document.getElementById("live-fps");
  if (fpsEl) fpsEl.textContent = `${data.fps} FPS`;

  const totalEl = document.getElementById("live-session-total");
  if (totalEl) totalEl.textContent = data.total_count || 0;

  if (data.session_counts) {
    for (const [cname, cnt] of Object.entries(data.session_counts)) {
      const el = document.getElementById(`live-cnt-${cname}`);
      if (el) el.textContent = cnt;
    }
  }

  // Update Topbar Badges
  const camBadge = document.getElementById("badge-camera");
  if (data.camera_status === "running") {
    camBadge.className = "badge badge-success";
    camBadge.innerHTML = '<span class="badge-dot"></span> Camera Active';
  } else {
    camBadge.className = "badge badge-warning";
    camBadge.innerHTML = '<span class="badge-dot"></span> Camera Idle';
  }

  const modelBadge = document.getElementById("badge-model");
  if (data.model_status === "ready") {
    modelBadge.className = "badge badge-success";
    modelBadge.innerHTML = '<span class="badge-dot"></span> Model Ready';
  } else if (data.model_status === "demo") {
    modelBadge.className = "badge badge-info";
    modelBadge.innerHTML = '<span class="badge-dot"></span> Demo Detector';
  } else {
    modelBadge.className = "badge badge-purple";
    modelBadge.innerHTML = '<span class="badge-dot"></span> Model Training...';
  }
}

// Camera Controls
async function startCamera() {
  const btnStart = document.getElementById("btn-start-cam");
  const btnStop = document.getElementById("btn-stop-cam");
  btnStart.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/camera/start`, { method: "POST" });
    const data = await res.json();
    
    const streamImg = document.getElementById("live-video-stream");
    const placeholder = document.getElementById("live-placeholder");
    streamImg.src = `${API_BASE}/api/camera/stream?t=${Date.now()}`;
    streamImg.style.display = "block";
    placeholder.style.display = "none";

    btnStart.style.display = "none";
    btnStop.style.display = "inline-flex";
    btnStop.disabled = false;
  } catch (err) {
    alert("Gagal memulai kamera: " + err.message);
  } finally {
    btnStart.disabled = false;
  }
}

async function stopCamera() {
  const btnStart = document.getElementById("btn-start-cam");
  const btnStop = document.getElementById("btn-stop-cam");
  btnStop.disabled = true;

  try {
    await fetch(`${API_BASE}/api/camera/stop`, { method: "POST" });
    
    const streamImg = document.getElementById("live-video-stream");
    const placeholder = document.getElementById("live-placeholder");
    streamImg.src = "";
    streamImg.style.display = "none";
    placeholder.style.display = "flex";

    btnStop.style.display = "none";
    btnStart.style.display = "inline-flex";
    btnStart.disabled = false;
  } catch (err) {
    alert("Gagal menghentikan kamera: " + err.message);
  } finally {
    btnStop.disabled = false;
  }
}

// Dashboard Data Loading (KPI, Macro Categories, & Charts)
async function loadDashboardData() {
  try {
    const [summaryRes, chartsRes] = await Promise.all([
      fetch(`${API_BASE}/api/dashboard/summary`),
      fetch(`${API_BASE}/api/dashboard/charts?hours=24`)
    ]);

    const summary = await summaryRes.json();
    const charts = await chartsRes.json();

    // Update KPI cards
    document.getElementById("kpi-total-detections").textContent = summary.total_detections;
    document.getElementById("notif-unread-count").textContent = summary.recent_notifications_count;

    // Update Macro Category Banner counts
    if (summary.macro_counts) {
      document.getElementById("macro-count-anorganik").textContent = summary.macro_counts.Anorganik || 0;
      document.getElementById("macro-count-organik").textContent = summary.macro_counts.Organik || 0;
      document.getElementById("macro-count-berbahaya").textContent = summary.macro_counts.Berbahaya || 0;
    }

    // Update 6 Official Class Detail Cards
    summary.class_counts.forEach(c => {
      const el = document.getElementById(`count-${c.class_name}`);
      if (el) el.textContent = c.count;
    });

    renderCharts(charts);
  } catch (err) {
    console.error("Error loading dashboard data", err);
  }
}

function renderCharts(chartData) {
  const ctxTimeline = document.getElementById("chart-timeline")?.getContext("2d");
  const ctxDist = document.getElementById("chart-distribution")?.getContext("2d");

  if (!ctxTimeline || !ctxDist) return;

  // 1. Timeline Chart (Futuristic Blue to Purple Gradient)
  const labels = chartData.timeline.map(p => p.label);
  const values = chartData.timeline.map(p => p.value);

  if (timelineChart) {
    timelineChart.data.labels = labels;
    timelineChart.data.datasets[0].data = values;
    timelineChart.update();
  } else {
    timelineChart = new Chart(ctxTimeline, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Deteksi Objek",
          data: values,
          borderColor: "#7C3AED",
          backgroundColor: "rgba(124, 58, 237, 0.08)",
          borderWidth: 2.5,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: "#2563EB",
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: "#f1f5f9" }, ticks: { color: "#64748b" } },
          y: { grid: { color: "#f1f5f9" }, ticks: { color: "#64748b", precision: 0 } }
        }
      }
    });
  }

  // 2. Distribution Doughnut Chart
  const distLabels = chartData.distribution.map(d => `${d.class_name} [${d.macro_category || 'Anorganik'}]`);
  const distValues = chartData.distribution.map(d => d.count);
  const distColors = chartData.distribution.map(d => d.color);

  if (distributionChart) {
    distributionChart.data.labels = distLabels;
    distributionChart.data.datasets[0].data = distValues;
    distributionChart.data.datasets[0].backgroundColor = distColors;
    distributionChart.update();
  } else {
    distributionChart = new Chart(ctxDist, {
      type: "doughnut",
      data: {
        labels: distLabels,
        datasets: [{
          data: distValues,
          backgroundColor: distColors,
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: "#475569", boxWidth: 10, font: { size: 10 } } }
        }
      }
    });
  }
}

// Detection History Table with Macro Category Filter & Badges
async function loadDetections() {
  const macroFilter = document.getElementById("filter-macro")?.value || "";
  const classFilter = document.getElementById("filter-class")?.value || "";
  const confFilter = document.getElementById("filter-conf")?.value || "";

  let url = `${API_BASE}/api/detections?page=${currentPage}&limit=15`;
  if (macroFilter) url += `&macro_category=${encodeURIComponent(macroFilter)}`;
  if (classFilter) url += `&class_name=${classFilter}`;
  if (confFilter) url += `&min_confidence=${confFilter}`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    const tbody = document.getElementById("history-table-body");
    tbody.innerHTML = "";

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:#64748b; padding:32px;">Belum ada riwayat deteksi yang sesuai filter.</td></tr>`;
      return;
    }

    data.items.forEach(item => {
      const col = CLASS_COLORS[item.class_name] || "#2563EB";
      const macro = item.macro_category || "Anorganik";
      const macroStyle = MACRO_INFO[macro] || MACRO_INFO["Anorganik"];
      const dt = new Date(item.detected_at).toLocaleString();

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>#${item.id}</strong></td>
        <td>${dt}</td>
        <td><span class="class-tag" style="background:${col}18; color:${col}; border:1px solid ${col}40">${item.class_name}</span></td>
        <td><span class="class-tag" style="background:${macroStyle.bg}; color:${macroStyle.color}; border:1px solid ${macroStyle.color}40">${macroStyle.icon} ${macro}</span></td>
        <td><strong>${Math.round(item.confidence * 100)}%</strong></td>
        <td>${item.track_id ? `#${item.track_id}` : '-'}</td>
        <td><code>${item.event_type}</code></td>
        <td>
          ${item.snapshot_path ? `<a href="/${item.snapshot_path}" target="_blank" class="btn btn-outline btn-sm">Lihat Foto</a>` : '<span style="color:#94a3b8">-</span>'}
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById("history-page-info").textContent = `Halaman ${data.page} dari ${Math.ceil(data.total / 15) || 1} (${data.total} total event)`;
  } catch (err) {
    console.error("Error loading history", err);
  }
}

function prevHistoryPage() {
  if (currentPage > 1) {
    currentPage--;
    loadDetections();
  }
}

function nextHistoryPage() {
  currentPage++;
  loadDetections();
}

// Root Cause Analysis (RCA) Module
async function loadRCA() {
  try {
    const res = await fetch(`${API_BASE}/api/rca`);
    const data = await res.json();

    // Summary counts
    document.getElementById("rca-count-active").textContent = data.summary.active || 0;
    document.getElementById("rca-count-investigating").textContent = data.summary.investigating || 0;
    document.getElementById("rca-count-resolved").textContent = data.summary.resolved || 0;

    const container = document.getElementById("rca-diagnostics-container");
    container.innerHTML = "";

    data.diagnostics.forEach(diag => {
      const card = document.createElement("div");
      card.className = "rca-card";

      // 5-Whys HTML
      const whysHtml = diag.five_whys.map((step, idx) => `
        <div class="why-step">
          <strong>Why ${idx + 1}:</strong> ${step}
        </div>
      `).join("");

      // Fishbone Ishikawa HTML
      const fishboneKeys = Object.keys(diag.ishikawa);
      const fishboneHtml = fishboneKeys.map(cat => `
        <div class="fishbone-box">
          <div class="fishbone-cat">${cat}</div>
          <ul class="fishbone-list">
            ${diag.ishikawa[cat].map(item => `<li>${item}</li>`).join("")}
          </ul>
        </div>
      `).join("");

      // Corrective & Preventive HTML
      const correctiveHtml = diag.corrective_actions.map(a => `<li>${a}</li>`).join("");
      const preventiveHtml = diag.preventive_actions.map(a => `<li>${a}</li>`).join("");

      // Status badge style
      let statusBadgeClass = "badge-danger";
      if (diag.status === "investigating") statusBadgeClass = "badge-warning";
      if (diag.status === "resolved") statusBadgeClass = "badge-success";

      card.innerHTML = `
        <div class="rca-card-header">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="rca-id">${diag.id}</span>
            <div class="rca-title">${diag.title}</div>
            <span class="badge ${diag.category === 'Berbahaya' ? 'badge-purple' : 'badge-info'}">${diag.category}</span>
          </div>
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="badge ${statusBadgeClass}">${diag.status.toUpperCase()}</span>
            <select onchange="updateRCAStatus('${diag.id}', this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.78rem;">
              <option value="active" ${diag.status === 'active' ? 'selected' : ''}>Aktif</option>
              <option value="investigating" ${diag.status === 'investigating' ? 'selected' : ''}>Investigasi</option>
              <option value="resolved" ${diag.status === 'resolved' ? 'selected' : ''}>Terselesaikan</option>
            </select>
          </div>
        </div>

        <div class="rca-problem">
          <strong>Pernyataan Masalah (Problem Statement):</strong><br>
          ${diag.problem_statement}
        </div>

        <div style="font-weight:700; font-size:0.92rem; color:#4338ca; margin-top:14px;">
          ⏳ Analisis 5-Whys (Mengapa Hal Tersebut Terjadi?):
        </div>
        <div class="whys-timeline">
          ${whysHtml}
        </div>

        <div style="font-weight:700; font-size:0.92rem; color:#2563eb; margin-top:18px;">
          🐟 Diagram Tulang Ikan Ishikawa (Fishbone 5M+1E):
        </div>
        <div class="fishbone-grid">
          ${fishboneHtml}
        </div>

        <div class="capa-grid">
          <div class="capa-box corrective">
            <div class="capa-title" style="color:#2563eb;">⚡ Tindakan Korektif Cepat (Immediate Corrective Action):</div>
            <ul style="margin-left:18px; font-size:0.83rem; color:#334155; line-height:1.4;">${correctiveHtml}</ul>
          </div>
          <div class="capa-box preventive">
            <div class="capa-title" style="color:#7c3aed;">🛡️ Tindakan Pencegahan Sistemik (Preventive Action):</div>
            <ul style="margin-left:18px; font-size:0.83rem; color:#334155; line-height:1.4;">${preventiveHtml}</ul>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading RCA", err);
  }
}

async function updateRCAStatus(diagnosticId, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/api/rca/${diagnosticId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      loadRCA();
    }
  } catch (err) {
    alert("Gagal memperbarui status RCA: " + err.message);
  }
}

// AI Chatbot Functionality (Tab & Floating Widget)
function toggleChatModal() {
  const modal = document.getElementById("chat-float-modal");
  modal.classList.toggle("open");
  if (modal.classList.contains("open")) {
    document.getElementById("chat-float-input").focus();
  }
}

function sendFloatPrompt(promptText) {
  const input = document.getElementById("chat-float-input");
  input.value = promptText;
  sendChatMessage("float");
}

function sendChatPrompt(promptText) {
  const input = document.getElementById("chat-tab-input");
  input.value = promptText;
  sendChatMessage("tab");
}

function openChatWithPrompt(promptText) {
  switchTab("chatbot");
  const input = document.getElementById("chat-tab-input");
  input.value = promptText;
  sendChatMessage("tab");
}

async function sendChatMessage(source = "tab") {
  const inputId = source === "tab" ? "chat-tab-input" : "chat-float-input";
  const containerId = source === "tab" ? "chat-messages-container" : "chat-float-messages";
  const promptsId = source === "tab" ? "chat-tab-prompts" : "chat-float-prompts";

  const input = document.getElementById(inputId);
  const text = input.value.trim();
  if (!text) return;

  const container = document.getElementById(containerId);

  // Append user bubble
  const userBubble = document.createElement("div");
  userBubble.className = "chat-bubble user";
  userBubble.textContent = text;
  container.appendChild(userBubble);
  input.value = "";
  container.scrollTop = container.scrollHeight;

  // Append thinking indicator
  const thinkingBubble = document.createElement("div");
  thinkingBubble.className = "chat-bubble bot";
  thinkingBubble.innerHTML = "<em>EcoBot sedang menganalisis data...</em>";
  container.appendChild(thinkingBubble);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();

    // Replace thinking bubble with formatted bot reply
    thinkingBubble.innerHTML = formatChatReply(data.reply);
    container.scrollTop = container.scrollHeight;

    // Render suggested action pills if available
    if (data.suggested_actions && data.suggested_actions.length > 0) {
      const promptsBox = document.getElementById(promptsId);
      if (promptsBox) {
        promptsBox.innerHTML = "";
        data.suggested_actions.forEach(action => {
          const pill = document.createElement("span");
          pill.className = "chat-prompt-pill";
          pill.textContent = action;
          pill.onclick = () => {
            input.value = action;
            sendChatMessage(source);
          };
          promptsBox.appendChild(pill);
        });
      }
    }
  } catch (err) {
    thinkingBubble.innerHTML = `<span style="color:red">Gagal menghubungi EcoBot AI: ${err.message}</span>`;
  }
}

function formatChatReply(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

// Notifications
async function loadNotifications() {
  try {
    const res = await fetch(`${API_BASE}/api/notifications?limit=50`);
    const notifs = await res.json();

    const list = document.getElementById("notifications-container");
    list.innerHTML = "";

    if (!notifs || notifs.length === 0) {
      list.innerHTML = `<div style="text-align:center; color:#64748b; padding:40px;">Tidak ada notifikasi sistem saat ini.</div>`;
      return;
    }

    notifs.forEach(n => {
      const dt = new Date(n.created_at).toLocaleString();
      const div = document.createElement("div");
      div.className = `notif-item ${n.is_read ? '' : 'unread'}`;
      div.style.cssText = "background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:16px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:flex-start;";
      div.innerHTML = `
        <div>
          <div style="font-weight:700; color:#1e1b4b; margin-bottom:4px;">${n.title}</div>
          <div style="font-size:0.86rem; color:#475569;">${n.message}</div>
          <div style="font-size:0.75rem; color:#94a3b8; margin-top:6px;">${dt} &bull; Tipe: <code>${n.type}</code></div>
        </div>
        <div>
          ${!n.is_read ? `<button onclick="markNotificationRead(${n.id})" class="btn btn-outline btn-sm">Tandai Dibaca</button>` : '<span style="color:#94a3b8; font-size:0.75rem;">Sudah dibaca</span>'}
        </div>
      `;
      list.appendChild(div);
    });
  } catch (err) {
    console.error("Error loading notifications", err);
  }
}

async function markNotificationRead(id) {
  try {
    await fetch(`${API_BASE}/api/notifications/${id}/read`, { method: "PATCH" });
    loadNotifications();
    loadDashboardData();
  } catch (err) {
    console.error("Failed to mark read", err);
  }
}

async function markAllNotificationsRead() {
  try {
    await fetch(`${API_BASE}/api/notifications/read-all`, { method: "POST" });
    loadNotifications();
    loadDashboardData();
  } catch (err) {
    console.error("Failed to mark all read", err);
  }
}

// PDF Reports
async function generateReport() {
  const btn = document.getElementById("btn-generate-report");
  btn.disabled = true;
  btn.textContent = "Sedang Membuat PDF...";

  try {
    const res = await fetch(`${API_BASE}/api/reports/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: "Laporan Monitoring Pemilahan Sampah & K3 - EcoSort AI"
      })
    });
    if (!res.ok) throw new Error("Gagal membuat laporan");
    await res.json();
    alert("Laporan PDF resmi berhasil dibuat dengan rincian kategori Organik, Anorganik, dan Berbahaya!");
    loadReports();
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Buat Laporan PDF Baru";
  }
}

async function loadReports() {
  try {
    const res = await fetch(`${API_BASE}/api/reports`);
    const reports = await res.json();

    const tbody = document.getElementById("reports-table-body");
    tbody.innerHTML = "";

    if (!reports || reports.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#64748b; padding:30px;">Belum ada laporan PDF yang digenerate. Klik tombol "Buat Laporan PDF Baru" di atas.</td></tr>`;
      return;
    }

    reports.forEach(r => {
      const dt = new Date(r.created_at).toLocaleString();
      const pStart = new Date(r.period_start).toLocaleDateString();
      const pEnd = new Date(r.period_end).toLocaleDateString();
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>#${r.id}</td>
        <td>${dt}</td>
        <td>${pStart} s/d ${pEnd}</td>
        <td><span class="badge badge-success">Selesai</span></td>
        <td>
          <a href="/api/reports/${r.id}/download" target="_blank" class="btn btn-primary btn-sm">Unduh PDF</a>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading reports", err);
  }
}

// Settings
async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/settings`);
    const s = await res.json();

    document.getElementById("setting-conf-val").textContent = s.confidence_threshold;
    document.getElementById("setting-conf-slider").value = s.confidence_threshold;

    document.getElementById("setting-line-val").textContent = s.virtual_line_y;
    document.getElementById("setting-line-slider").value = s.virtual_line_y;

    document.getElementById("setting-demo-toggle").checked = s.is_demo_mode;
    document.getElementById("setting-model-status-text").textContent = `${s.model_status.toUpperCase()} - ${s.model_message}`;
  } catch (err) {
    console.error("Error loading settings", err);
  }
}

async function saveSettings() {
  const conf = parseFloat(document.getElementById("setting-conf-slider").value);
  const line = parseFloat(document.getElementById("setting-line-slider").value);
  const demo = document.getElementById("setting-demo-toggle").checked;

  try {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        confidence_threshold: conf,
        virtual_line_y: line,
        demo_mode: demo
      })
    });
    await res.json();
    alert("Konfigurasi berhasil disimpan!");
    loadSettings();
  } catch (err) {
    alert("Gagal menyimpan konfigurasi: " + err.message);
  }
}

async function triggerModelReload() {
  try {
    const res = await fetch(`${API_BASE}/api/settings/reload-model`, { method: "POST" });
    const data = await res.json();
    alert(`Status Reload: ${data.status}\n${data.message}`);
    loadSettings();
  } catch (err) {
    alert("Gagal reload model: " + err.message);
  }
}

// Requirements Docs Viewer
async function loadRequirementsList() {
  try {
    const res = await fetch(`${API_BASE}/api/requirements`);
    const files = await res.json();

    const nav = document.getElementById("docs-file-list");
    nav.innerHTML = "";

    files.forEach((f, idx) => {
      const btn = document.createElement("button");
      btn.className = `doc-btn ${idx === 0 ? 'active' : ''}`;
      btn.textContent = f.title;
      btn.onclick = () => {
        document.querySelectorAll(".doc-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        loadDocContent(f.filename);
      };
      nav.appendChild(btn);
    });

    if (files.length > 0) {
      loadDocContent(files[0].filename);
    }
  } catch (err) {
    console.error("Error loading docs list", err);
  }
}

async function loadDocContent(filename) {
  const container = document.getElementById("doc-content-viewer");
  container.innerHTML = "Memuat dokumen...";

  try {
    const res = await fetch(`${API_BASE}/api/requirements/${filename}`);
    const data = await res.json();
    container.innerHTML = parseSimpleMarkdown(data.content);
  } catch (err) {
    container.innerHTML = `<p style="color:red">Gagal memuat dokumen: ${err.message}</p>`;
  }
}

function parseSimpleMarkdown(md) {
  let html = md
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n\n/gim, '</p><p>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>');
  return `<p>${html}</p>`;
}
