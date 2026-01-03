const API_BASE = "http://localhost:8000";

let projects = [];
let jobs = [];
let selectedProjectId = null;
let selectedJobId = null;

const projectTitle = document.getElementById("project-title");
const projectNote = document.getElementById("project-note");
const projectList = document.getElementById("project-list");
const jobList = document.getElementById("job-list");
const jobTitle = document.getElementById("job-title");
const jobPurpose = document.getElementById("job-purpose");
const jobTone = document.getElementById("job-tone");
const jobDuration = document.getElementById("job-duration");
const jobStatus = document.getElementById("job-status");
const jobProgressText = document.getElementById("job-progress-text");
const jobProgress = document.getElementById("job-progress");
const jobCredits = document.getElementById("job-credits");
const jobLogs = document.getElementById("job-logs");
const artifactList = document.getElementById("artifact-list");
const reviewHistory = document.getElementById("review-history");

const newProjectButton = document.getElementById("new-project");
const newJobButton = document.getElementById("new-job");
const approveButton = document.getElementById("approve-job");
const rejectButton = document.getElementById("reject-job");
const uploadForm = document.getElementById("upload-form");
const slidesFile = document.getElementById("slides-file");
const audioFile = document.getElementById("audio-file");

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

const loadProjects = async () => {
  projects = await fetchJson(`${API_BASE}/projects`);
  renderProjects();
  if (projects.length > 0) {
    selectProject(projects[0].id);
  } else {
    projectTitle.textContent = "プロジェクト";
    projectNote.textContent = "プロジェクトを作成してください。";
    jobList.innerHTML = "";
  }
};

const loadJobs = async () => {
  if (!selectedProjectId) return;
  jobs = await fetchJson(`${API_BASE}/projects/${selectedProjectId}/jobs`);
  renderJobs();
  if (jobs.length > 0) {
    selectJob(jobs[0].id);
  } else {
    clearJobDetail();
  }
};

const renderProjects = () => {
  projectList.innerHTML = "";
  projects.forEach((project) => {
    const card = document.createElement("article");
    card.className = `card${project.id === selectedProjectId ? " selected" : ""}`;
    card.dataset.projectId = project.id;

    const title = document.createElement("div");
    title.className = "card-title";
    title.textContent = project.title;

    const summary = document.createElement("p");
    summary.className = "muted";
    summary.textContent = project.reference_note || "参照メモなし";

    card.append(title, summary);
    card.addEventListener("click", () => selectProject(project.id));
    projectList.append(card);
  });
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
  jobCredits.textContent = "-";
  jobLogs.innerHTML = "";
  artifactList.innerHTML = "";
  reviewHistory.textContent = "";
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

const selectProject = async (projectId) => {
  selectedProjectId = projectId;
  const project = projects.find((item) => item.id === projectId);
  if (project) {
    projectTitle.textContent = project.title;
    projectNote.textContent = project.reference_note || "参照メモなし";
  }
  renderProjects();
  await loadJobs();
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

  const latestUsage = job.billing[0];
  if (latestUsage) {
    jobCredits.textContent = `${latestUsage.duration_seconds} 秒 · 使用量記録`;
  } else {
    jobCredits.textContent = "-";
  }

  jobLogs.innerHTML = "";
  job.logs.forEach((entry) => {
    const li = document.createElement("li");
    li.textContent = entry;
    jobLogs.append(li);
  });

  artifactList.innerHTML = "";
  job.artifacts.forEach((artifact) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = `${API_BASE}/jobs/${job.id}/artifacts/${artifact.id}/download`;
    link.textContent = `${artifact.artifact_type} をダウンロード`;
    link.target = "_blank";
    li.append(link);
    artifactList.append(li);
  });

  reviewHistory.innerHTML = job.reviews
    .map(
      (review) =>
        `${review.created_at.slice(0, 16).replace("T", " ")} : ${review.decision} ${review.comment || ""}`
    )
    .join("<br />");

  renderJobs();
};

newProjectButton.addEventListener("click", async () => {
  const title = window.prompt("プロジェクト名を入力してください");
  if (!title) return;
  const reference = window.prompt("参照情報メモ（任意）") || "";
  await fetchJson(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, reference_note: reference }),
  });
  await loadProjects();
});

newJobButton.addEventListener("click", async () => {
  if (!selectedProjectId) {
    window.alert("プロジェクトを選択してください");
    return;
  }
  const title = window.prompt("ジョブ名を入力してください");
  if (!title) return;
  const purpose = window.prompt("目的を入力してください") || "";
  const tone = window.prompt("口調（例: 丁寧/カジュアル）") || "丁寧";
  const duration = window.prompt("目標尺（秒）", "60");
  if (!duration) return;

  await fetchJson(`${API_BASE}/projects/${selectedProjectId}/jobs`, {
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

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedJobId) {
    window.alert("ジョブを選択してください");
    return;
  }
  if (!slidesFile.files[0] || !audioFile.files[0]) {
    window.alert("slides.pdf と audio.zip を選択してください");
    return;
  }
  const formData = new FormData();
  formData.append("slides_pdf", slidesFile.files[0]);
  formData.append("audio_zip", audioFile.files[0]);

  await fetchJson(`${API_BASE}/jobs/${selectedJobId}/upload`, {
    method: "POST",
    body: formData,
  });
  await selectJob(selectedJobId);
});

approveButton.addEventListener("click", async () => {
  if (!selectedJobId) return;
  await fetchJson(`${API_BASE}/jobs/${selectedJobId}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision: "approved" }),
  });
  await selectJob(selectedJobId);
});

rejectButton.addEventListener("click", async () => {
  if (!selectedJobId) return;
  const comment = window.prompt("差戻しコメントを入力してください") || "";
  await fetchJson(`${API_BASE}/jobs/${selectedJobId}/reviews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision: "rejected", comment }),
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

loadProjects();
