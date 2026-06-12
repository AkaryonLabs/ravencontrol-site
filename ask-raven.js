const form = document.querySelector("#askRavenForm");
const statusBox = document.querySelector("#intakeStatus");

const API_BASE =
  window.RAVEN_API_URL ||
  localStorage.getItem("RAVEN_API_URL") ||
  "http://127.0.0.1:8765";

function setStatus(kind, message) {
  statusBox.className = `intake-status ${kind}`;
  statusBox.textContent = message;
}

function buildMailto(payload) {
  const body = Object.entries(payload)
    .map(([key, value]) => `${key}: ${value}`)
    .join("\n");
  return `mailto:verify@ravencontrol.com?subject=${encodeURIComponent(
    "Ask Raven intake"
  )}&body=${encodeURIComponent(body)}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const payload = Object.fromEntries(data.entries());
  payload.consent = data.get("consent") === "on";
  payload.api_provider = "claude";

  if (!payload.consent) {
    setStatus("error", "Please check the consent box before sending.");
    return;
  }

  setStatus("pending", "Sending to Raven...");

  try {
    const response = await fetch(`${API_BASE}/api/public-intake`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Raven backend returned ${response.status}`);
    }

    const result = await response.json();
    setStatus(
      "success",
      `Received. Case ${result.case_id} is ${result.risk} risk. ${result.customer_response}`
    );
    form.reset();
  } catch (error) {
    setStatus(
      "error",
      "The Raven case system is not online right now. Opening email fallback..."
    );
    window.location.href = buildMailto(payload);
  }
});
