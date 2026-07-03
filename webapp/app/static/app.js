const sessionId = "web-" + Math.random().toString(36).slice(2);
let currentFilter = "";

const taskList = document.getElementById("task-list");
const taskForm = document.getElementById("task-form");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

const PRIORITY_LABELS = { high: "عالية", normal: "عادية", low: "منخفضة" };

async function loadTasks() {
  const url = currentFilter ? `/api/tasks?status=${currentFilter}` : "/api/tasks";
  const tasks = await (await fetch(url)).json();
  taskList.innerHTML = "";
  if (tasks.length === 0) {
    taskList.innerHTML = '<li style="color:#64748b">لا توجد مهام</li>';
    return;
  }
  for (const t of tasks) {
    const li = document.createElement("li");
    li.className = t.status === "done" ? "done" : "";

    const check = document.createElement("input");
    check.type = "checkbox";
    check.checked = t.status === "done";
    check.onchange = async () => {
      await fetch(`/api/tasks/${t.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: check.checked ? "done" : "pending" }),
      });
      loadTasks();
    };

    const title = document.createElement("span");
    title.className = "title";
    title.textContent = t.title;

    const badge = document.createElement("span");
    badge.className = `badge ${t.priority}`;
    badge.textContent = PRIORITY_LABELS[t.priority] || t.priority;

    const del = document.createElement("button");
    del.className = "icon-btn";
    del.textContent = "🗑️";
    del.title = "حذف";
    del.onclick = async () => {
      await fetch(`/api/tasks/${t.id}`, { method: "DELETE" });
      loadTasks();
    };

    li.append(check, title, badge, del);
    taskList.appendChild(li);
  }
}

taskForm.onsubmit = async (e) => {
  e.preventDefault();
  const title = document.getElementById("task-title").value.trim();
  const priority = document.getElementById("task-priority").value;
  if (!title) return;
  await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, priority }),
  });
  taskForm.reset();
  loadTasks();
};

document.querySelectorAll(".filter").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".filter").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.status;
    loadTasks();
  };
});

function addMessage(text, cls, tools) {
  const div = document.createElement("div");
  div.className = `msg ${cls}`;
  div.textContent = text;
  if (tools && tools.length) {
    const span = document.createElement("span");
    span.className = "tools";
    span.textContent = "🔧 الأدوات المستخدمة: " + tools.join("، ");
    div.appendChild(span);
  }
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

chatForm.onsubmit = async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  addMessage(message, "user");
  chatInput.value = "";
  const btn = chatForm.querySelector("button");
  btn.disabled = true;
  const thinking = addMessage("... جاري التفكير", "bot");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const data = await res.json();
    thinking.remove();
    if (!res.ok) {
      addMessage(data.detail || "حدث خطأ", "error");
    } else {
      addMessage(data.reply, "bot", data.tools_used);
      loadTasks(); // the agent may have changed the tasks
    }
  } catch {
    thinking.remove();
    addMessage("تعذر الاتصال بالخادم", "error");
  } finally {
    btn.disabled = false;
    chatInput.focus();
  }
};

loadTasks();
