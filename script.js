const tasks = [];
let nextId = 1;
const API_BASE = "http://localhost:8000/api/tasks";

const taskForm = document.getElementById("task-form");
const jsonInput = document.getElementById("json-input");
const tasksList = document.getElementById("tasks-list");
const strategySelect = document.getElementById("strategy");
const analyzeBtn = document.getElementById("analyze-btn");
const suggestBtn = document.getElementById("suggest-btn");
const errorBox = document.getElementById("error");
const statusBox = document.getElementById("status");

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.classList.remove("hidden");
  statusBox.classList.add("hidden");
}

function showStatus(msg) {
  statusBox.textContent = msg;
  statusBox.classList.remove("hidden");
  errorBox.classList.add("hidden");
}

function clearMessages() {
  errorBox.classList.add("hidden");
  statusBox.classList.add("hidden");
}

taskForm.addEventListener("submit", (e) => {
  e.preventDefault();
  clearMessages();

  const title = document.getElementById("title").value.trim();
  const due_date = document.getElementById("due_date").value || null;
  const estimated_hoursRaw = document.getElementById("estimated_hours").value;
  const importanceRaw = document.getElementById("importance").value;
  const depsText = document.getElementById("dependencies").value.trim();

  if (!title) {
    return showError("Title is required");
  }

  let estimated_hours = estimated_hoursRaw ? parseFloat(estimated_hoursRaw) : null;
  if (estimated_hours !== null && estimated_hours < 0) {
    return showError("Estimated hours must be non-negative");
  }

  let importance = importanceRaw ? parseInt(importanceRaw, 10) : null;
  if (importance !== null && (importance < 1 || importance > 10)) {
    return showError("Importance must be between 1 and 10");
  }

  let dependencies = [];
  if (depsText.length > 0) {
    dependencies = depsText
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
      .map((s) => parseInt(s, 10))
      .filter((n) => !isNaN(n));
  }

  const task = {
    id: nextId++,
    title,
    due_date,
    estimated_hours,
    importance,
    dependencies,
  };

  tasks.push(task);
  showStatus("Task added. Total tasks: " + tasks.length);
  taskForm.reset();
  renderTasks(tasks);
});

function getTasksForRequest() {
  const raw = jsonInput.value.trim();
  if (raw.length > 0) {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed;
      } else {
        showError("JSON input must be an array of tasks");
        return null;
      }
    } catch (e) {
      showError("Invalid JSON in bulk input");
      return null;
    }
  }

  if (tasks.length === 0) {
    showError("No tasks available. Add a task or paste JSON.");
    return null;
  }

  return tasks;
}

analyzeBtn.addEventListener("click", async () => {
  clearMessages();
  const taskList = getTasksForRequest();
  if (!taskList) return;

  const strategy = strategySelect.value;
  showStatus("Analyzing tasks...");

  try {
    const res = await fetch(`${API_BASE}/analyze/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tasks: taskList, strategy }),
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Request failed");
    }

    const data = await res.json();
    renderTasks(data.tasks || []);
    showStatus(`Analyzed ${data.count} task(s) using '${data.strategy}' strategy.`);
  } catch (err) {
    showError(err.message);
  }
});

suggestBtn.addEventListener("click", async () => {
  clearMessages();
  const taskList = getTasksForRequest();
  if (!taskList) return;

  const strategy = strategySelect.value;
  showStatus("Requesting suggestions...");

  try {
    const res = await fetch(`${API_BASE}/suggest/`, {
      method: "POST", // easier than GET-with-body
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tasks: taskList, strategy }),
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Request failed");
    }

    const data = await res.json();
    renderTasks(data.suggested || []);
    showStatus(`Showing top ${data.suggested.length} suggested task(s).`);
  } catch (err) {
    showError(err.message);
  }
});

function renderTasks(taskArray) {
  tasksList.innerHTML = "";
  if (!taskArray || taskArray.length === 0) {
    tasksList.innerHTML = "<p>No tasks to display.</p>";
    return;
  }

  taskArray.forEach((t) => {
    const card = document.createElement("div");
    card.classList.add("task-card");

    const score = typeof t.score === "number" ? t.score : 0;
    if (score >= 0.75) {
      card.classList.add("priority-high");
    } else if (score >= 0.4) {
      card.classList.add("priority-medium");
    } else {
      card.classList.add("priority-low");
    }

    const header = document.createElement("div");
    header.classList.add("task-header");

    const title = document.createElement("div");
    title.classList.add("task-title");
    title.textContent = t.title || "(No title)";

    const scoreEl = document.createElement("div");
    scoreEl.classList.add("task-score");
    scoreEl.textContent = "Score: " + score.toFixed(3);

    header.appendChild(title);
    header.appendChild(scoreEl);

    const meta = document.createElement("div");
    meta.classList.add("task-meta");
    meta.textContent =
      `ID: ${t.id ?? "-"} | Due: ${t.due_date ?? "N/A"} | ` +
      `Hours: ${t.estimated_hours ?? "N/A"} | ` +
      `Importance: ${t.importance ?? "N/A"} | ` +
      `Dependencies: ${(t.dependencies || []).join(", ") || "None"}`;

    const expl = document.createElement("div");
    expl.classList.add("task-explanation");
    expl.textContent = t.explanation || "";

    card.appendChild(header);
    card.appendChild(meta);
    card.appendChild(expl);

    tasksList.appendChild(card);
  });
}
