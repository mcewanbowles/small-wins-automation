import { API_URL } from "./constants";

async function unwrapResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed.");
  }
  return payload;
}

export async function fetchKeywords(platform, seed, goldOnly, storeLevel, winnableOnly) {
  const response = await fetch(`${API_URL}/api/keywords`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      platform,
      seed,
      gold_only: goldOnly,
      store_level: storeLevel,
      winnable_only: winnableOnly,
    }),
  });
  return unwrapResponse(response);
}

export async function auditListing(auditForm) {
  const tags = auditForm.tags
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const response = await fetch(`${API_URL}/api/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      platform: auditForm.platform || "tpt",
      title: auditForm.title,
      tags,
      description: auditForm.description,
    }),
  });
  return unwrapResponse(response);
}

export async function generateListing(form) {
  const response = await fetch(`${API_URL}/api/generate-listing`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      platform: form.platform,
      niche: form.niche,
      buyer_type: form.buyerType,
      product_description: form.productDescription,
      product_stage: form.productStage,
      seller_confidence: form.sellerConfidence,
    }),
  });
  return unwrapResponse(response);
}
