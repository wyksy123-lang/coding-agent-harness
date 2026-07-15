const statusFields = {
  mode: document.getElementById("mode-value"),
  status: document.getElementById("run-status-value"),
  phase: document.getElementById("phase-value"),
  test_status: document.getElementById("test-status-value"),
  passed: document.getElementById("passed-count-value"),
  failed: document.getElementById("failed-count-value"),
  failure_type: document.getElementById("failure-type-value"),
  failure_details: document.getElementById("failure-details-value"),
  round_number: document.getElementById("round-number-value"),
  strategy: document.getElementById("strategy-value"),
  stop_reason: document.getElementById("stop-reason-value"),
};
const failureTypeCard = document.getElementById("failure-type-card");
const failureDetailsCard = document.getElementById("failure-details-card");
const hitlList = document.getElementById("hitl-list");
const connectionStatus = document.getElementById("connection-status");
const currentEvent = document.getElementById("current-event-value");
const timelineList = document.getElementById("timeline-list");
const sensitiveNamePattern = /(api[_-]?key|token|secret|password|cwd|dir|directory)/i;
const sensitiveContentPattern = /(api[_-]?key|token|secret|password)\s*[:=]\s*\S+/gi;
const absolutePathPattern = /([A-Za-z]:\\\S+|\\\\\S+|\/\S+)/g;

const displayMap = {
  live: "本地实时",
  demo: "演示",
  idle: "空闲",
  "Not started": "未开始",
  Running: "运行中",
  "Awaiting approval": "等待审批",
  "Running tests": "测试中",
  Completed: "已完成",
  Failed: "已失败",
  running: "运行中",
  awaiting_approval: "等待审批",
  testing: "测试中",
  completed: "已完成",
  failed: "已失败",
  not_started: "未开始",
  passed: "已通过",
  error: "执行错误",
  PASS: "已通过",
  FAIL: "已失败",
  LLM_ERROR: "LLM_ERROR",
  LLM_API_ERROR: "LLM API 错误",
  LLM_RESPONSE_ERROR: "LLM 响应错误",
};

const eventNames = {
  task_started: "任务开始",
  round_started: "轮次开始",
  model_requested: "模型请求",
  model_response: "模型响应",
  model_error: "模型错误",
  tool_requested: "工具请求",
  tool_completed: "工具完成",
  tests_started: "测试开始",
  tests_completed: "测试完成",
  hitl_requested: "请求人工审批",
  hitl_resolved: "审批完成",
  run_finished: "任务结束",
};

function valueOrFallback(value, fallback = "—") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  const rendered = String(value);
  return ["unknown", "none", "null", "undefined"].includes(rendered.toLowerCase())
    ? fallback
    : rendered;
}

function localized(value, fallback = "—") {
  const rendered = valueOrFallback(value, fallback);
  return displayMap[rendered] || rendered;
}

function sanitizeForDisplay(name, value) {
  if (sensitiveNamePattern.test(name)) {
    return "[redacted]";
  }
  if (typeof value === "string") {
    return value
      .replace(sensitiveContentPattern, "$1=[redacted]")
      .replace(/\S*\.env\S*/g, "[redacted]")
      .replace(/C:\\Users\\\S+/g, "[redacted]")
      .replace(absolutePathPattern, "[redacted]");
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeForDisplay(name, item));
  }
  if (value && typeof value === "object") {
    const sanitized = {};
    for (const [childName, childValue] of Object.entries(value)) {
      sanitized[childName] = sanitizeForDisplay(childName, childValue);
    }
    return sanitized;
  }
  return value;
}

function renderStatus(status) {
  if (!status || typeof status !== "object") {
    return;
  }
  statusFields.mode.textContent = localized(status.mode);
  statusFields.status.textContent = localized(status.status);
  statusFields.phase.textContent = localized(status.phase);
  statusFields.test_status.textContent = localized(status.test_status || "not_started");
  const summary =
    status.test_summary && typeof status.test_summary === "object" ? status.test_summary : {};
  statusFields.passed.textContent = valueOrFallback(summary.passed);
  statusFields.failed.textContent = valueOrFallback(summary.failed);
  const failureType = valueOrFallback(status.failure_type, "");
  failureTypeCard.hidden = failureType === "";
  statusFields.failure_type.textContent = localized(failureType);
  const failureDetails = renderFailureDetails(status.failure_details);
  failureDetailsCard.hidden = failureDetails === "";
  statusFields.failure_details.textContent = failureDetails || "—";
  statusFields.round_number.textContent = valueOrFallback(status.round_number, "0");
  statusFields.strategy.textContent = valueOrFallback(status.strategy);
  statusFields.stop_reason.textContent = localized(status.stop_reason);
  renderHitl(Array.isArray(status.pending_hitl) ? status.pending_hitl : []);
}

function renderFailureDetails(details) {
  if (!Array.isArray(details) || details.length === 0) {
    return "";
  }
  return details
    .map((detail) => {
      if (!detail || typeof detail !== "object") {
        return "";
      }
      return valueOrFallback(detail.message, JSON.stringify(detail), "");
    })
    .filter(Boolean)
    .join("; ");
}

function renderTimeline(events) {
  const timeline = Array.isArray(events) ? events : [];
  timelineList.replaceChildren();
  if (timeline.length === 0) {
    currentEvent.textContent = "—";
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "暂无事件";
    timelineList.append(empty);
    return;
  }

  const latest = timeline[timeline.length - 1];
  currentEvent.textContent = eventLabel(latest);
  let lastRound = null;
  for (const event of timeline) {
    if (event.event_type === "task_started") {
      timelineList.append(timelineDivider("任务启动"));
    }
    if (
      event.round_index !== null &&
      event.round_index !== undefined &&
      event.round_index !== lastRound
    ) {
      timelineList.append(timelineDivider(`第 ${event.round_index} 轮`));
      lastRound = event.round_index;
    }
    if (event.event_type === "run_finished") {
      timelineList.append(timelineDivider("任务结束"));
    }
    const item = document.createElement("li");
    item.className = `timeline-node ${eventStyle(event)}`;
    if (event === latest) {
      item.classList.add("latest");
    }
    const symbol = document.createElement("span");
    symbol.className = "timeline-symbol";
    symbol.textContent = eventSymbol(event);
    const body = document.createElement("div");
    body.className = "timeline-body";
    const title = document.createElement("strong");
    title.textContent = eventLabel(event);
    const meta = document.createElement("small");
    meta.textContent = eventMeta(event);
    const summary = document.createElement("p");
    summary.textContent = valueOrFallback(event.summary);
    body.append(title, meta, summary);
    item.append(symbol, body);
    timelineList.append(item);
  }
}

function timelineDivider(label) {
  const item = document.createElement("li");
  item.className = "timeline-divider";
  item.textContent = label;
  return item;
}

function eventLabel(event) {
  if (!event || typeof event !== "object") {
    return "—";
  }
  const base = eventNames[event.event_type] || valueOrFallback(event.event_type, "事件");
  if (event.tool_name) {
    return `${base}：${event.tool_name}`;
  }
  return base;
}

function eventMeta(event) {
  const parts = [];
  const time = localTime(event.timestamp);
  if (time) {
    parts.push(time);
  }
  if (event.round_index !== null && event.round_index !== undefined) {
    parts.push(`第 ${event.round_index} 轮`);
  }
  if (event.test_status) {
    parts.push(localized(event.test_status));
  }
  if (event.hitl_decision) {
    parts.push(event.hitl_decision === "approved" ? "已批准" : "已拒绝");
  }
  if (event.stop_reason) {
    parts.push(`停止原因：${event.stop_reason}`);
  }
  return parts.join(" · ");
}

function localTime(timestamp) {
  if (!timestamp) {
    return "";
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleTimeString();
}

function eventStyle(event) {
  if (event.event_type === "model_error" || event.phase === "failed") {
    return "error";
  }
  if (event.event_type === "hitl_requested" || event.event_type === "hitl_resolved") {
    return "approval";
  }
  if (event.test_status === "failed" || event.test_status === "error") {
    return "warning";
  }
  if (event.phase === "completed" || event.test_status === "passed") {
    return "success";
  }
  return "running";
}

function eventSymbol(event) {
  const style = eventStyle(event);
  if (style === "success") {
    return "✓";
  }
  if (style === "warning" || style === "error") {
    return "✕";
  }
  if (style === "approval") {
    return "!";
  }
  if (event.event_type === "run_finished") {
    return "■";
  }
  return "●";
}

function renderHitl(requests) {
  hitlList.replaceChildren();
  if (requests.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "暂无待审批操作";
    hitlList.append(empty);
    return;
  }

  for (const request of requests) {
    const hitlRequest = request && typeof request === "object" ? request : {};
    const item = document.createElement("article");
    item.className = "hitl-item";

    const title = document.createElement("h3");
    const requestId = valueOrFallback(hitlRequest.request_id, "未知请求");
    const action =
      hitlRequest.action && typeof hitlRequest.action === "object" ? hitlRequest.action : {};
    title.textContent = `${valueOrFallback(action.tool_name, "工具")} - ${requestId}`;

    const args = document.createElement("pre");
    args.textContent = JSON.stringify(sanitizeForDisplay("args", action.args || {}), null, 2);

    const error = document.createElement("p");
    error.className = "hitl-error";
    error.hidden = true;

    const controls = document.createElement("div");
    controls.className = "hitl-actions";
    controls.append(
      decisionButton(requestId, "approve", "批准", error),
      decisionButton(requestId, "deny", "拒绝", error),
    );

    item.append(title, args, error, controls);
    hitlList.append(item);
  }
}

function decisionButton(requestId, decision, label, errorElement) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", async () => {
    const controls = button.closest(".hitl-actions");
    const buttons = controls ? controls.querySelectorAll("button") : [button];
    errorElement.hidden = true;
    buttons.forEach((control) => {
      control.disabled = true;
    });
    try {
      const response = await fetch(`/api/hitl/${encodeURIComponent(requestId)}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision }),
      });
      if (!response.ok) {
        throw new Error(`审批失败 HTTP ${response.status}`);
      }
    } catch (error) {
      errorElement.textContent = error instanceof Error ? error.message : "审批失败";
      errorElement.hidden = false;
      buttons.forEach((control) => {
        control.disabled = false;
      });
    }
  });
  return button;
}

function connectWebSocket() {
  connectionStatus.textContent = "连接中";
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  socket.addEventListener("open", () => {
    connectionStatus.textContent = "已连接";
  });
  socket.addEventListener("message", (event) => {
    let message;
    try {
      message = JSON.parse(event.data);
    } catch {
      return;
    }
    if (message && message.type === "snapshot" && typeof message.snapshot === "object") {
      renderStatus(message.snapshot);
      renderTimeline(message.timeline || message.snapshot.timeline || []);
    } else if (message && message.type === "event" && typeof message.snapshot === "object") {
      renderStatus(message.snapshot);
      renderTimeline(message.timeline || []);
    } else if (message && message.type === "status" && typeof message.status === "object") {
      renderStatus(message.status);
    }
  });
  socket.addEventListener("error", () => {
    connectionStatus.textContent = "离线";
  });
  socket.addEventListener("close", () => {
    connectionStatus.textContent = "重新连接中";
    window.setTimeout(connectWebSocket, 1000);
  });
}

connectWebSocket();
