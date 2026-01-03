const jobs = [
  {
    id: "job-1",
    title: "セキュリティオンボーディング",
    summary: "承認待ち · 7 スライド",
    status: "承認待ち",
    progressCurrent: 3,
    progressTotal: 8,
    credits: "42 分 · 120 クレジット",
    approver: "佐藤 祐子",
    logs: ["キュー → 入力検証", "構成案の生成", "台本の生成"],
  },
  {
    id: "job-2",
    title: "人事コンプライアンス",
    summary: "スライド生成中 · 4 スライド",
    status: "スライド生成中",
    progressCurrent: 4,
    progressTotal: 8,
    credits: "24 分 · 70 クレジット",
    approver: "山田 太郎",
    logs: ["入力検証完了", "構成案の生成", "台本の生成", "スライド生成中"],
  },
  {
    id: "job-3",
    title: "プロダクトチュートリアル",
    summary: "キュー待ち · 10 スライド",
    status: "キュー待ち",
    progressCurrent: 1,
    progressTotal: 8,
    credits: "18 分 · 52 クレジット",
    approver: "未設定",
    logs: ["ジョブ登録"],
  },
];

const jobList = document.getElementById("job-list");
const jobTitle = document.getElementById("job-title");
const jobStatus = document.getElementById("job-status");
const jobProgressText = document.getElementById("job-progress-text");
const jobProgress = document.getElementById("job-progress");
const jobCredits = document.getElementById("job-credits");
const jobApprover = document.getElementById("job-approver");
const jobLogs = document.getElementById("job-logs");
const newJobButton = document.getElementById("new-job");
const navItems = document.querySelectorAll(".nav-item");

const renderJobs = () => {
  jobList.innerHTML = "";
  jobs.forEach((job, index) => {
    const card = document.createElement("article");
    card.className = `card${index === 0 ? " selected" : ""}`;
    card.dataset.jobId = job.id;

    const title = document.createElement("div");
    title.className = "card-title";
    title.textContent = job.title;

    const summary = document.createElement("p");
    summary.className = "muted";
    summary.textContent = job.summary;

    card.append(title, summary);
    card.addEventListener("click", () => selectJob(job.id));
    jobList.append(card);
  });
};

const updateProgressDots = (current, total) => {
  jobProgress.innerHTML = "";
  for (let i = 1; i <= total; i += 1) {
    const dot = document.createElement("span");
    dot.className = `dot${i <= current ? " active" : ""}`;
    jobProgress.append(dot);
  }
};

const selectJob = (jobId) => {
  const job = jobs.find((item) => item.id === jobId);
  if (!job) return;

  jobTitle.textContent = job.title;
  jobStatus.textContent = job.status;
  jobProgressText.textContent = `${job.progressCurrent} / ${job.progressTotal} ステップ`;
  jobCredits.textContent = job.credits;
  jobApprover.textContent = job.approver;

  jobLogs.innerHTML = "";
  job.logs.forEach((entry) => {
    const li = document.createElement("li");
    li.textContent = entry;
    jobLogs.append(li);
  });

  updateProgressDots(job.progressCurrent, job.progressTotal);

  document.querySelectorAll(".card").forEach((card) => {
    card.classList.toggle("selected", card.dataset.jobId === jobId);
  });
};

newJobButton.addEventListener("click", () => {
  const title = window.prompt("新しいジョブ名を入力してください");
  if (!title) return;

  const newJob = {
    id: `job-${Date.now()}`,
    title,
    summary: "キュー待ち · 0 スライド",
    status: "キュー待ち",
    progressCurrent: 1,
    progressTotal: 8,
    credits: "0 分 · 0 クレジット",
    approver: "未設定",
    logs: ["ジョブ登録"],
  };

  jobs.unshift(newJob);
  renderJobs();
  selectJob(newJob.id);
});

navItems.forEach((item) => {
  item.addEventListener("click", (event) => {
    event.preventDefault();
    navItems.forEach((nav) => nav.classList.remove("active"));
    item.classList.add("active");
  });
});

renderJobs();
selectJob(jobs[0].id);
