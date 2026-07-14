const statusFields = {
  phase: document.getElementById("phase-value"),
  test_status: document.getElementById("test-status-value"),
  failure_type: document.getElementById("failure-type-value"),
  round_number: document.getElementById("round-number-value"),
  strategy: document.getElementById("strategy-value"),
  stop_reason: document.getElementById("stop-reason-value"),
};
const hitlList = document.getElementById("hitl-list");

function valueOrFallback(value, fallback) {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

function renderStatus(status) {
  statusFields.phase.textContent = valueOrFallback(status.phase, "idle");
  statusFields.test_status.textContent = valueOrFallback(status.test_status, "unknown");
  statusFields.failure_type.textContent = valueOrFallback(status.failure_type, "none");
  statusFields.round_number.textContent = valueOrFallback(status.round_number, "0");
  statusFields.strategy.textContent = valueOrFallback(status.strategy, "none");
  statusFields.stop_reason.textContent = valueOrFallback(status.stop_reason, "running");
  renderHitl(status.pending_hitl || []);
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
    const item = document.createElement("article");
    item.className = "hitl-item";

    const title = document.createElement("h3");
    title.textContent = `${request.action.tool_name} · ${request.request_id}`;

    const args = document.createElement("pre");
    args.textContent = JSON.stringify(request.action.args, null, 2);

    const controls = document.createElement("div");
    controls.className = "hitl-actions";
    controls.append(
      decisionButton(request.request_id, "approve", "Approve"),
      decisionButton(request.request_id, "deny", "Deny"),
    );

    item.append(title, args, controls);
    hitlList.append(item);
  }
}

function decisionButton(requestId, decision, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", async () => {
    button.disabled = true;
    await fetch(`/api/hitl/${encodeURIComponent(requestId)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ decision }),
    });
  });
  return button;
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "status") {
      renderStatus(message.status);
    }
  });
  socket.addEventListener("close", () => {
    window.setTimeout(connectWebSocket, 1000);
  });
}

connectWebSocket();
