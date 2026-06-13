let state = { clients: [], cases: [] };
let selectedCaseId = null;

const $ = (selector) => document.querySelector(selector);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

async function loadState() {
  state = await api("/api/state");
  if (!selectedCaseId && state.cases?.length) {
    selectedCaseId = state.cases[0].id;
  }
  renderClients();
  renderCases();
  renderCaseDetail();
  renderOpsStrip();
  fillClientSelect();
}

function renderOpsStrip() {
  const cases = state.cases || [];
  const openCases = cases.filter((item) => item.status !== "Resolved").length;
  const needsGuardian = cases.filter((item) => ["Needs Guardian", "Escalated"].includes(item.status)).length;
  const highRisk = cases.filter((item) => ["High", "Critical"].includes(item.review?.risk)).length;
  const newestDelivery = cases[0] ? getDeliveryStatus(cases[0].email_delivery) : { label: "Ready", className: "ok" };
  $("#openCaseCount").textContent = openCases;
  $("#needsGuardianCount").textContent = needsGuardian;
  $("#highRiskCount").textContent = highRisk;
  $("#deliveryHealth").textContent = newestDelivery.label;
  $("#deliveryHealth").className = newestDelivery.className;
}

function fillClientSelect() {
  const select = $("#clientSelect");
  select.innerHTML = state.clients
    .map((client) => `<option value="${client.id}">${escapeHtml(client.name)} - ${escapeHtml(client.plan)}</option>`)
    .join("");
}

function renderClients() {
  $("#clientList").innerHTML = state.clients
    .map(
      (client) => `
        <article class="client-item">
          <h3>${escapeHtml(client.name)}</h3>
          <div class="meta">${escapeHtml(client.plan)} • ${escapeHtml(client.segment)} • ${escapeHtml(client.raven_address)}</div>
          <div class="tags">${client.pause_rules.map((rule) => `<span class="tag">${escapeHtml(rule)}</span>`).join("")}</div>
        </article>
      `
    )
    .join("");
}

function renderCases() {
  const cases = state.cases || [];
  $("#caseList").innerHTML = cases.length
    ? cases.map(renderCase).join("")
    : `<div class="empty-state"><strong>No cases yet</strong><p>Run a review to create the first case.</p></div>`;
}

function renderCase(item) {
  const review = item.review || {};
  const delivery = getDeliveryStatus(item.email_delivery);
  const message = (item.message || "").replace(/\s+/g, " ").trim();
  return `
    <article class="case-item ${item.id === selectedCaseId ? "selected" : ""}" data-case-id="${escapeHtml(item.id)}">
      <div>
        <div class="case-head">
          <h3>${escapeHtml(item.client_name || "Unknown client")}</h3>
          <span class="delivery-badge ${delivery.className}">${escapeHtml(delivery.label)}</span>
        </div>
        <div class="meta">${escapeHtml(item.channel)} • ${escapeHtml(item.sender || "Unknown sender")} • ${formatDate(item.created_at)}</div>
        <p>${escapeHtml(message.slice(0, 190))}${message.length > 190 ? "..." : ""}</p>
        <div class="tags">
          <span class="tag">${escapeHtml(item.status)}</span>
          <span class="tag">${escapeHtml(review.fraud_bucket || "Needs review")}</span>
          ${(review.red_flags || []).slice(0, 5).map((flag) => `<span class="tag">${escapeHtml(flag)}</span>`).join("")}
        </div>
      </div>
      <span class="pill ${escapeHtml(review.risk || "Low")}">${escapeHtml(review.risk || "Low")}</span>
    </article>
  `;
}

function renderCaseDetail() {
  const target = $("#caseDetail");
  const item = state.cases.find((entry) => entry.id === selectedCaseId);
  if (!item) {
    target.className = "case-detail empty-state";
    target.innerHTML = `<strong>No case selected</strong><p>Select a case from the queue to review it.</p>`;
    return;
  }

  const review = item.review || {};
  const guardian = item.guardian_review || {};
  const delivery = item.email_delivery || {};
  const deliveryStatus = getDeliveryStatus(delivery);
  target.className = "case-detail";
  target.innerHTML = `
    <div class="detail-grid">
      <article class="detail-card">
        <div class="risk-top">
          <div>
            <h3>${escapeHtml(item.client_name)}</h3>
            <div class="meta">${escapeHtml(item.channel)} • ${escapeHtml(item.sender || "Unknown sender")} • ${escapeHtml(item.id)}</div>
          </div>
          <span class="pill ${escapeHtml(review.risk || "Low")}">${escapeHtml(review.risk || "Low")}</span>
        </div>
        <div class="case-summary">
          <div><span>Status</span><strong>${escapeHtml(item.status)}</strong></div>
          <div><span>Decision</span><strong>${escapeHtml(guardian.final_decision || "Not decided")}</strong></div>
          <div><span>Email</span><strong class="${deliveryStatus.className}">${escapeHtml(deliveryStatus.label)}</strong></div>
        </div>
        <div class="kv">
          <div><strong>Submitted item</strong>${escapeHtml(item.message || "")}</div>
          <div><strong>Fraud bucket</strong>${escapeHtml(review.fraud_bucket || "Needs review")}</div>
          <div><strong>Red flags</strong><div class="tags">${renderTags(review.red_flags || [])}</div></div>
          <div><strong>Safe verification path</strong>${escapeHtml(review.safe_verification_path || "")}</div>
          <div><strong>Axiom draft response</strong>${escapeHtml(review.customer_response || "")}</div>
          <details>
            <summary>Email delivery details</summary>
            <pre class="delivery-json">${escapeHtml(JSON.stringify(delivery, null, 2))}</pre>
          </details>
        </div>
      </article>

      <form id="guardianForm" class="guardian-form">
        <div class="quick-decisions" aria-label="Quick final decisions">
          <button type="button" data-decision="Likely scam">Likely Scam</button>
          <button type="button" data-decision="Needs more verification">Needs Verification</button>
          <button type="button" data-decision="Likely safe">Appears Safe</button>
        </div>
        <label>
          Case status
          <select name="status">
            ${["Received", "Auto Reviewed", "Needs Guardian", "Waiting on Client", "Escalated", "Resolved"].map((status) => `<option ${status === item.status ? "selected" : ""}>${status}</option>`).join("")}
          </select>
        </label>
        <label>
          Guardian
          <input name="guardian" value="${escapeAttr(guardian.guardian || "Guardian Mia")}" />
        </label>
        <label>
          Final decision
          <select name="final_decision">
            ${["", "Likely safe", "Suspicious", "Likely scam", "Confirmed scam", "Needs more verification"].map((value) => `<option value="${escapeAttr(value)}" ${value === (guardian.final_decision || "") ? "selected" : ""}>${value || "Choose decision"}</option>`).join("")}
          </select>
        </label>
        <label>
          Escalation
          <select name="escalation">
            ${["None", "Senior Guardian", "Fraud Specialist", "Family Contact", "Bank/Platform", "Attorney Referral"].map((value) => `<option ${value === (guardian.escalation || "None") ? "selected" : ""}>${value}</option>`).join("")}
          </select>
        </label>
        <label>
          Guardian notes
          <textarea name="guardian_notes" rows="5">${escapeHtml(guardian.guardian_notes || "")}</textarea>
        </label>
        <label>
          Customer response sent or ready to send
          <textarea name="customer_response" rows="5">${escapeHtml(guardian.customer_response || review.customer_response || "")}</textarea>
        </label>
        <label class="check">
          <input type="checkbox" name="response_sent" ${guardian.response_sent ? "checked" : ""} />
          Response sent to customer
        </label>
        <button type="submit">Save Guardian Review</button>
      </form>
    </div>
  `;

  $("#guardianForm").addEventListener("submit", saveGuardianReview);
  document.querySelectorAll("[data-decision]").forEach((button) => {
    button.addEventListener("click", applyQuickDecision);
  });
}

function renderResult(caseItem) {
  const review = caseItem.review;
  $("#resultPanel").innerHTML = `
    <div class="risk-card">
      <div class="risk-top">
        <div>
          <h2>${escapeHtml(review.fraud_bucket)}</h2>
          <div class="meta">Source: ${escapeHtml(review.review_source)}${review.model ? ` • ${escapeHtml(review.model)}` : ""}</div>
        </div>
        <span class="pill ${escapeHtml(review.risk)}">${escapeHtml(review.risk)}</span>
      </div>
      ${review.api_error ? `<div class="tag">API fallback: ${escapeHtml(review.api_error)}</div>` : ""}
      <div class="kv">
        <div>
          <strong>Red flags</strong>
          <div class="tags">${(review.red_flags || []).map((flag) => `<span class="tag">${escapeHtml(flag)}</span>`).join("") || "<span class='tag'>None detected</span>"}</div>
        </div>
        <div>
          <strong>Safe verification path</strong>
          ${escapeHtml(review.safe_verification_path || "")}
        </div>
        <div>
          <strong>Guardian recommendation</strong>
          ${escapeHtml(review.guardian_recommendation || "")}
        </div>
        <div>
          <strong>Customer response</strong>
          ${escapeHtml(review.customer_response || "")}
        </div>
        <div>
          <strong>Detected amounts / links</strong>
          ${[...(review.amounts || []), ...(review.links || [])].map(escapeHtml).join(", ") || "None"}
        </div>
      </div>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

function renderTags(items) {
  return items.length
    ? items.map((flag) => `<span class="tag">${escapeHtml(flag)}</span>`).join("")
    : `<span class="tag">None detected</span>`;
}

function getDeliveryStatus(delivery = {}) {
  if (!delivery || !Object.keys(delivery).length) return { label: "No email", className: "muted" };
  const internalOk = Boolean(delivery.internal?.id);
  const customerOk = Boolean(delivery.customer?.id);
  const hasError = Boolean(delivery.internal?.error || delivery.customer?.error);
  if (internalOk && customerOk) return { label: "Sent", className: "ok" };
  if (hasError) return { label: "Email issue", className: "bad" };
  if (internalOk || customerOk) return { label: "Partial", className: "warn" };
  return { label: "Pending", className: "muted" };
}

function formatDate(value) {
  if (!value) return "No date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No date";
  return date.toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function applyQuickDecision(event) {
  const form = $("#guardianForm");
  const decision = event.currentTarget.dataset.decision;
  form.elements.final_decision.value = decision;
  if (decision === "Likely scam") {
    form.elements.status.value = "Needs Guardian";
    form.elements.escalation.value = "Senior Guardian";
  } else if (decision === "Needs more verification") {
    form.elements.status.value = "Waiting on Client";
    form.elements.escalation.value = "None";
  } else {
    form.elements.status.value = "Resolved";
    form.elements.escalation.value = "None";
  }
}

async function saveGuardianReview(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.response_sent = form.get("response_sent") === "on";
  const updated = await api(`/api/cases/${selectedCaseId}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const index = state.cases.findIndex((item) => item.id === updated.id);
  if (index >= 0) state.cases[index] = updated;
  renderCases();
  renderCaseDetail();
  renderOpsStrip();
}

$("#reviewForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  $("#resultPanel").innerHTML = `<div class="empty-state"><strong>Reviewing...</strong><p>Axiom is checking risk, red flags, and safe next steps.</p></div>`;
  try {
    const caseItem = await api("/api/review", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderResult(caseItem);
    await loadState();
  } catch (error) {
    $("#resultPanel").innerHTML = `<div class="empty-state"><strong>Review failed</strong><p>${escapeHtml(error.message)}</p></div>`;
  }
});

$("#refreshBtn").addEventListener("click", loadState);
$("#openNewestBtn").addEventListener("click", () => {
  if (!state.cases?.length) return;
  selectedCaseId = state.cases[0].id;
  renderCases();
  renderCaseDetail();
  location.hash = "case-detail";
});

$("#caseList").addEventListener("click", (event) => {
  const card = event.target.closest("[data-case-id]");
  if (!card) return;
  selectedCaseId = card.dataset.caseId;
  renderCases();
  renderCaseDetail();
  location.hash = "case-detail";
});

loadState();
