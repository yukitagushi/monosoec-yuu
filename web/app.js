const API_BASE = "/api";

let jobs = [];
let selectedJobId = null;

const jobList = document.getElementById("job-list");
const jobTitle = document.getElementById("job-title");
const jobPurpose = document.getElementById("job-purpose");
const jobTone = document.getElementById("job-tone");
const jobDuration = document.getElementById("job-duration");
const jobStatus = document.getElementById("job-status");
const jobProgressText = document.getElementById("job-progress-text");
const jobProgress = document.getElementById("job-progress");
const jobLogs = document.getElementById("job-logs");

const newJobButton = document.getElementById("new-job");
const renderButton = document.getElementById("render-job");
const navItems = document.querySelectorAll(".nav-item");

const statusLabel = (status) => {
  const map = {
    queued: "キュー待ち",
    running_render: "レンダリング中",
    needs_review: "承認待ち",
    approved: "承認済み",
    rejected: "差戻し",
    failed: "失敗",
  };
  return map[status] || status;
};

const fetchJson = async (url, options) => {
  const response = await fetch(url, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "API error");
  }
  return response.json();
};

const loadJobs = async () => {
  jobs = await fetchJson(`${API_BASE}/jobs`);
  renderJobs();
  if (jobs.length > 0) {
    await selectJob(jobs[0].id);
  } else {
    clearJobDetail();
  }
};

const renderJobs = () => {
  jobList.innerHTML = "";
  jobs.forEach((job) => {
    const card = document.createElement("article");
    card.className = `card${job.id === selectedJobId ? " selected" : ""}`;
    card.dataset.jobId = job.id;

    const title = document.createElement("div");
    title.className = "card-title";
    title.textContent = job.title;

    const summary = document.createElement("p");
    summary.className = "muted";
    summary.textContent = `${statusLabel(job.status)} · ${job.progress_percent}%`;

    card.append(title, summary);
    card.addEventListener("click", () => selectJob(job.id));
    jobList.append(card);
  });
};

const clearJobDetail = () => {
  selectedJobId = null;
  jobTitle.textContent = "-";
  jobPurpose.textContent = "-";
  jobTone.textContent = "-";
  jobDuration.textContent = "-";
  jobStatus.textContent = "-";
  jobProgressText.textContent = "-";
  jobProgress.innerHTML = "";
  jobLogs.innerHTML = "";
};

const updateProgressDots = (percent) => {
  const totalDots = 10;
  const activeDots = Math.round(percent / 10);
  jobProgress.innerHTML = "";
  for (let i = 1; i <= totalDots; i += 1) {
    const dot = document.createElement("span");
    dot.className = `dot${i <= activeDots ? " active" : ""}`;
    jobProgress.append(dot);
  }
};

const selectJob = async (jobId) => {
  selectedJobId = jobId;
  const job = await fetchJson(`${API_BASE}/jobs/${jobId}`);
  jobTitle.textContent = job.title;
  jobPurpose.textContent = job.purpose;
  jobTone.textContent = job.tone;
  jobDuration.textContent = `${job.target_duration_seconds} 秒`;
  jobStatus.textContent = statusLabel(job.status);
  jobProgressText.textContent = `${job.progress_percent}%`;
  updateProgressDots(job.progress_percent);

  jobLogs.innerHTML = "";
  job.logs.forEach((entry) => {
    const li = document.createElement("li");
    li.textContent = entry;
    jobLogs.append(li);
  });

  renderJobs();
};

newJobButton.addEventListener("click", async () => {
  const title = window.prompt("ジョブ名を入力してください");
  if (!title) return;
  const purpose = window.prompt("目的を入力してください") || "";
  const tone = window.prompt("口調（例: 丁寧/カジュアル）") || "丁寧";
  const duration = window.prompt("目標尺（秒）", "60");
  if (!duration) return;

  await fetchJson(`${API_BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      purpose,
      tone,
      target_duration_seconds: Number(duration),
    }),
  });
  await loadJobs();
});

renderButton.addEventListener("click", async () => {
  if (!selectedJobId) {
    window.alert("ジョブを選択してください");
    return;
  }
  await fetchJson(`${API_BASE}/jobs/${selectedJobId}/render`, {
    method: "POST",
  });
  await selectJob(selectedJobId);
});

navItems.forEach((item) => {
  item.addEventListener("click", (event) => {
    event.preventDefault();
    navItems.forEach((nav) => nav.classList.remove("active"));
    item.classList.add("active");
  });
});

loadJobs();
