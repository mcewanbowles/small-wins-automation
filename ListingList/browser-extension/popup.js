const defaults = {
  apiUrl: "http://localhost:8000",
  appUrl: "http://localhost:5173",
};

const apiUrlEl = document.getElementById("apiUrl");
const appUrlEl = document.getElementById("appUrl");
const seedEl = document.getElementById("seed");
const platformEl = document.getElementById("platform");
const nicheEl = document.getElementById("niche");
const buyerTypeEl = document.getElementById("buyerType");
const descriptionEl = document.getElementById("description");
const keywordsResultEl = document.getElementById("keywordsResult");
const listingResultEl = document.getElementById("listingResult");
const statusEl = document.getElementById("status");

const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const findKeywordsBtn = document.getElementById("findKeywordsBtn");
const copyKeywordsBtn = document.getElementById("copyKeywordsBtn");
const generateListingBtn = document.getElementById("generateListingBtn");
const copyListingBtn = document.getElementById("copyListingBtn");
const openAppBtn = document.getElementById("openAppBtn");

function setStatus(message, kind = "info") {
  statusEl.textContent = message;
  statusEl.className = `status status-${kind}`;
}

function normalizedBase(url) {
  return url.trim().replace(/\/$/, "");
}

async function loadSettings() {
  const stored = await chrome.storage.local.get(defaults);
  apiUrlEl.value = stored.apiUrl || defaults.apiUrl;
  appUrlEl.value = stored.appUrl || defaults.appUrl;
}

async function saveSettings() {
  const apiUrl = normalizedBase(apiUrlEl.value || defaults.apiUrl);
  const appUrl = normalizedBase(appUrlEl.value || defaults.appUrl);
  await chrome.storage.local.set({ apiUrl, appUrl });
  apiUrlEl.value = apiUrl;
  appUrlEl.value = appUrl;
  setStatus("Settings saved.");
}

async function getApiUrl() {
  const stored = await chrome.storage.local.get(defaults);
  return normalizedBase(stored.apiUrl || defaults.apiUrl);
}

async function getAppUrl() {
  const stored = await chrome.storage.local.get(defaults);
  return normalizedBase(stored.appUrl || defaults.appUrl);
}

async function unwrapResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed.");
  }
  return payload;
}

function friendlyError(error, apiUrl) {
  const text = String(error?.message || "").toLowerCase();
  if (text.includes("failed to fetch") || text.includes("networkerror")) {
    return `Could not connect to ${apiUrl}. Make sure backend is running and URL is correct.`;
  }
  if (text.includes("cors")) {
    return "Request blocked by browser security (CORS). Check backend CORS settings for extension requests.";
  }
  return error?.message || "Request failed.";
}

async function copyText(value, successMessage) {
  if (!value.trim()) {
    setStatus("Nothing to copy yet.", "warn");
    return;
  }
  try {
    await navigator.clipboard.writeText(value);
    setStatus(successMessage, "success");
  } catch {
    setStatus("Could not copy. Try selecting and copying manually.", "error");
  }
}

async function onFindKeywords() {
  const seed = seedEl.value.trim();
  if (!seed) {
    setStatus("Add a seed topic first.");
    return;
  }

  findKeywordsBtn.disabled = true;
  keywordsResultEl.textContent = "Loading...";

  try {
    const apiUrl = await getApiUrl();
    const response = await fetch(`${apiUrl}/api/keywords`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        platform: "tpt",
        seed,
        gold_only: false,
        store_level: "new_store",
        winnable_only: true,
      }),
    });
    const payload = await unwrapResponse(response);
    const rows = (payload.items || []).slice(0, 8).map((item) => `${item.phrase} (${item.verdict})`);
    keywordsResultEl.textContent = rows.length ? rows.join("\n") : "No keywords returned.";
    setStatus("Keyword check complete.", "success");
  } catch (error) {
    keywordsResultEl.textContent = "";
    setStatus(friendlyError(error, await getApiUrl()), "error");
  } finally {
    findKeywordsBtn.disabled = false;
  }
}

async function onGenerateListing() {
  const description = descriptionEl.value.trim();
  if (description.length < 20) {
    setStatus("Add at least 20 characters in product description.");
    return;
  }

  generateListingBtn.disabled = true;
  listingResultEl.textContent = "Loading...";

  try {
    const apiUrl = await getApiUrl();
    const response = await fetch(`${apiUrl}/api/generate-listing`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        platform: platformEl.value,
        niche: nicheEl.value.trim() || "Special Education",
        buyer_type: buyerTypeEl.value.trim() || "SPED teacher",
        product_description: description,
        product_stage: "Product is finished",
        seller_confidence: "Beginner - I need step-by-step help",
      }),
    });
    const payload = await unwrapResponse(response);
    const lines = [
      `Title: ${payload.title || ""}`,
      "",
      `Tags: ${(payload.tags || []).join(", ")}`,
    ];
    listingResultEl.textContent = lines.join("\n");
    setStatus("Listing draft generated.", "success");
  } catch (error) {
    listingResultEl.textContent = "";
    setStatus(friendlyError(error, await getApiUrl()), "error");
  } finally {
    generateListingBtn.disabled = false;
  }
}

async function onOpenApp() {
  const appUrl = await getAppUrl();
  try {
    await chrome.tabs.create({ url: appUrl });
  } catch {
    setStatus("Could not open app URL. Check App URL in settings.", "error");
  }
}

async function onCopyKeywords() {
  await copyText(keywordsResultEl.textContent || "", "Keyword results copied.");
}

async function onCopyListing() {
  await copyText(listingResultEl.textContent || "", "Listing results copied.");
}

saveSettingsBtn.addEventListener("click", saveSettings);
findKeywordsBtn.addEventListener("click", onFindKeywords);
copyKeywordsBtn.addEventListener("click", onCopyKeywords);
generateListingBtn.addEventListener("click", onGenerateListing);
copyListingBtn.addEventListener("click", onCopyListing);
openAppBtn.addEventListener("click", onOpenApp);

loadSettings();
