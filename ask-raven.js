const form = document.querySelector("#askRavenForm");
const statusBox = document.querySelector("#intakeStatus");
const fileInput = document.querySelector('input[name="screenshot"]');
const filePreview = document.querySelector("#filePreview");

const API_BASE =
  window.RAVEN_API_URL ||
  localStorage.getItem("RAVEN_API_URL") ||
  (location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8765"
    : "https://ravencontrol-site.onrender.com");

let uploadedFile = null;

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

// Handle file selection and preview
fileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) {
    uploadedFile = null;
    filePreview.innerHTML = "";
    return;
  }

  // Validate file size (max 10 MB)
  const MAX_SIZE = 10 * 1024 * 1024;
  if (file.size > MAX_SIZE) {
    setStatus("error", `File is too large. Maximum 10 MB allowed.`);
    fileInput.value = "";
    return;
  }

  // Validate file type
  const validTypes = ["image/png", "image/jpeg", "image/jpg", "image/gif", "application/pdf"];
  if (!validTypes.includes(file.type)) {
    setStatus("error", "Please upload PNG, JPG, GIF, or PDF files only.");
    fileInput.value = "";
    return;
  }

  // Convert to base64
  try {
    const reader = new FileReader();
    reader.onload = (e) => {
      uploadedFile = {
        name: file.name,
        type: file.type,
        size: file.size,
        data: e.target.result, // base64 encoded
      };

      // Show file preview
      const icon = file.type === "application/pdf" ? "📄" : "🖼️";
      const sizeKB = (file.size / 1024).toFixed(1);
      
      filePreview.innerHTML = `
        <div class="file-item">
          <span class="file-item-icon">${icon}</span>
          <div class="file-item-info">
            <span class="file-item-name">${file.name}</span>
            <span class="file-item-size">${sizeKB} KB</span>
          </div>
          <button type="button" class="file-item-remove" aria-label="Remove file">×</button>
        </div>
      `;

      // Add remove button handler
      filePreview.querySelector(".file-item-remove").addEventListener("click", (e) => {
        e.preventDefault();
        uploadedFile = null;
        fileInput.value = "";
        filePreview.innerHTML = "";
      });
    };
    reader.readAsDataURL(file);
  } catch (error) {
    setStatus("error", "Failed to read file. Please try again.");
    fileInput.value = "";
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const payload = Object.fromEntries(data.entries());
  payload.consent = data.get("consent") === "on";
  payload.api_provider = "claude";
  payload.offer = "free_one_time_scam_check";

  // Add uploaded file to payload if present
  if (uploadedFile) {
    payload.screenshot = {
      name: uploadedFile.name,
      type: uploadedFile.type,
      size: uploadedFile.size,
      data: uploadedFile.data, // base64
    };
  }

  if (!payload.consent) {
    setStatus("error", "Please check the consent box before sending.");
    return;
  }

  if (!payload.email || !payload.phone) {
    setStatus("error", "Please enter a real email and phone number for the free scam check.");
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
      `Received. Check your email for Raven's safety response. Case ${result.case_id} is ${result.risk} risk.`
    );
    form.reset();
    filePreview.innerHTML = "";
    uploadedFile = null;
  } catch (error) {
    setStatus(
      "error",
      "The Raven case system is not online right now. Opening email fallback..."
    );
    window.location.href = buildMailto(payload);
  }
});
