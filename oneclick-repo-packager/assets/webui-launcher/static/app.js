const statusEl = document.getElementById("status");
const logsEl = document.getElementById("logs");
const installBtn = document.getElementById("installBtn");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

if (!HAS_INSTALL) installBtn.disabled = true;
if (!HAS_RUN) startBtn.disabled = true;

async function post(url) {
  const res = await fetch(url, { method: "POST" });
  return res.json();
}

async function refresh() {
  const status = await fetch("/api/status").then(r => r.json());
  statusEl.textContent = status.running ? "Status: running" : "Status: stopped";

  const logs = await fetch("/api/logs").then(r => r.json());
  logsEl.textContent = (logs.lines || []).join("
");
  logsEl.scrollTop = logsEl.scrollHeight;
}

installBtn.addEventListener("click", async () => {
  installBtn.disabled = true;
  await post("/api/install");
  installBtn.disabled = !HAS_INSTALL;
});

startBtn.addEventListener("click", async () => {
  await post("/api/start");
});

stopBtn.addEventListener("click", async () => {
  await post("/api/stop");
});

refresh();
setInterval(refresh, 1000);
