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
const hitlList = document.getElementById("hitl-list");
const connectionStatus = document.getElementById("connection-status");
const currentEvent = document.getElementById("current-event-value");
const timelineList = document.getElementById("timeline-list");
const sensitiveNamePattern = /(api[_-]?key|token|secret|password|path|cwd|dir|directory|file)/i;
const sensitiveContentPattern = /(api[_-]?key|token|secret|password)\s*[:=]\s*\S+/gi;
const pathLikePattern = /([A-Za-z]:\\\S+|\\\\\S+|\/\S+|\S*[\\/]\S+|[\w.-]+\.[A-Za-z0-9]{1,8})/g;

function valueOrFallback(value, fallback) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  const rendered = String(value);
  return ["unknown", "none", "null", "undefined"].includes(rendered.toLowerCase())
    ? fallback
    : rendered;
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
      .replace(pathLikePattern, "[redacted]");
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
  statusFields.mode.textContent = valueOrFallback(status.mode, "Not available");
  statusFields.status.textContent = valueOrFallback(status.status, "Not available");
  statusFields.phase.textContent = valueOrFallback(status.phase, "Not available");
  statusFields.test_status.textContent = valueOrFallback(status.test_status, "Not available");
  const summary =
    status.test_summary && typeof status.test_summary === "object" ? status.test_summary : {};
  statusFields.passed.textContent = valueOrFallback(summary.passed, "0");
  statusFields.failed.textContent = valueOrFallback(summary.failed, "0");
  statusFields.failure_type.textContent = valueOrFallback(status.failure_type, "Not available");
  statusFields.failure_details.textContent = renderFailureDetails(status.failure_details);
  statusFields.round_number.textContent = valueOrFallback(status.round_number, "0");
  statusFields.strategy.textContent = valueOrFallback(status.strategy, "Not available");
  statusFields.stop_reason.textContent = valueOrFallback(status.stop_reason, "Not available");
  renderHitl(Array.isArray(status.pending_hitl) ? status.pending_hitl : []);
}

function renderFailureDetails(details) {
  if (!Array.isArray(details) || details.length === 0) {
    return "Not available";
  }
  return details
    .map((detail) => {
      if (!detail || typeof detail !== "object") {
        return "";
      }
      return valueOrFallback(detail.message, JSON.stringify(detail));
    })
    .filter(Boolean)
    .join("; ");
}

function renderTimeline(events) {
  const timeline = Array.isArray(events) ? events : [];
  timelineList.replaceChildren();
  if (timeline.length === 0) {
    currentEvent.textContent = "Not available";
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "No events yet";
    timelineList.append(empty);
    return;
  }

  const latest = timeline[timeline.length - 1];
  currentEvent.textContent = eventLabel(latest);
  for (const event of timeline.slice(-20)) {
    const item = document.createElement("li");
    item.textContent = eventLabel(event);
    timelineList.append(item);
  }
}

function eventLabel(event) {
  if (!event || typeof event !== "object") {
    return "Not available";
  }
  const type = valueOrFallback(event.event_type, "event");
  const summary = valueOrFallback(event.summary, "");
  const round = event.round_index === null || event.round_index === undefined ? "" : `r${event.round_index}`;
  return [round, type, summary].filter(Boolean).join(" - ");
}

function renderHitl(requests) {
  hitlList.replaceChildren();
  if (requests.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No pending approvals";
    hitlList.append(empty);
    return;
  }

  for (const request of requests) {
    const hitlRequest = request && typeof request === "object" ? request : {};
    const item = document.createElement("article");
    item.className = "hitl-item";

    const title = document.createElement("h3");
    const requestId = valueOrFallback(hitlRequest.request_id, "unknown-request");
    const action =
      hitlRequest.action && typeof hitlRequest.action === "object" ? hitlRequest.action : {};
    title.textContent = `${valueOrFallback(action.tool_name, "tool")} - ${requestId}`;

    const args = document.createElement("pre");
    args.textContent = JSON.stringify(sanitizeForDisplay("args", action.args || {}), null, 2);

    const error = document.createElement("p");
    error.className = "hitl-error";
    error.hidden = true;

    const controls = document.createElement("div");
    controls.className = "hitl-actions";
    controls.append(
      decisionButton(requestId, "approve", "Approve", error),
      decisionButton(requestId, "deny", "Deny", error),
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
        throw new Error(`approval failed with HTTP ${response.status}`);
      }
    } catch (error) {
      errorElement.textContent = error instanceof Error ? error.message : "approval failed";
      errorElement.hidden = false;
      buttons.forEach((control) => {
        control.disabled = false;
      });
    }
  });
  return button;
}

function connectWebSocket() {
  connectionStatus.textContent = "Connecting";
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  socket.addEventListener("open", () => {
    connectionStatus.textContent = "Connected";
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
    connectionStatus.textContent = "Offline";
  });
  socket.addEventListener("close", () => {
    connectionStatus.textContent = "Reconnecting";
    window.setTimeout(connectWebSocket, 1000);
  });
}

connectWebSocket();
