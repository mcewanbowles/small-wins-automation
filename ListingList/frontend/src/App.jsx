import { useMemo, useRef, useState } from "react";
import { auditListing, fetchKeywords, fetchReverseIntel, generateListing } from "./api";
import {
  BUYER_TYPES,
  NICHES,
  PLATFORM_CAPABILITIES,
  PLATFORM_LIMITS,
  PLATFORM_OPTIONS,
  PRODUCT_VARIANT,
  PRODUCT_STAGES,
  SELLER_CONFIDENCE_LEVELS,
  STORE_LEVELS,
} from "./constants";

function CopyButton({ value, className = "" }) {
  const [copied, setCopied] = useState(false);

  async function copyNow() {
    if (!value) {
      return;
    }
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <button className={`ghost-btn ${className}`.trim()} onClick={copyNow} type="button">
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function VerdictBadge({ verdict }) {
  const map = {
    MAKE_THIS: { label: "BEST BET", className: "verdict-green" },
    WORTH_A_SHOT: { label: "POSSIBLE", className: "verdict-amber" },
    CROWDED: { label: "TOO CROWDED", className: "verdict-red" },
  };
  const entry = map[verdict] || map.CROWDED;
  return <span className={`verdict ${entry.className}`}>{entry.label}</span>;
}

function RecommendationBadge({ label }) {
  const map = {
    "Start Here": { className: "recommendation-start" },
    "Possible Next": { className: "recommendation-next" },
    "Avoid for Now": { className: "recommendation-avoid" },
  };
  const entry = map[label] || map["Possible Next"];
  return <span className={`recommendation-badge ${entry.className}`}>{label}</span>;
}

function ConfidenceBadge({ level }) {
  const map = {
    High: { className: "confidence-high" },
    Medium: { className: "confidence-medium" },
    Low: { className: "confidence-low" },
  };
  const entry = map[level] || map.Medium;
  return <span className={`confidence-badge ${entry.className}`}>{level} confidence</span>;
}

function keywordConfidence(row) {
  const hasSupply = row.tpt_supply_count !== null && row.tpt_supply_count !== undefined;
  const hasReviews = row.avg_top5_reviews !== null && row.avg_top5_reviews !== undefined;
  if (hasSupply && hasReviews) return "High";
  if (hasSupply || hasReviews) return "Medium";
  return "Low";
}

function formatSourceHits(sourceHits) {
  if (!Array.isArray(sourceHits) || sourceHits.length === 0) {
    return "";
  }
  const mapped = sourceHits
    .map((item) => String(item || "").toLowerCase().trim())
    .filter(Boolean)
    .map((item) => (item === "tpt" ? "TPT" : item === "google" ? "Google" : item));
  const unique = [...new Set(mapped)];
  if (!unique.length) {
    return "";
  }
  if (unique.length === 1) {
    return `Seen on ${unique[0]}`;
  }
  return `Seen on ${unique.join(" + ")}`;
}

const IDEA_SEED_EXAMPLES = [
  "social stories autism",
  "morning work",
  "adapted books",
  "behavior expectations",
  "visual schedule",
];

const ANGLE_SEED_EXAMPLES = [
  "christmas social stories",
  "christmas math centers",
  "halloween writing prompts",
  "valentines day activities",
  "end of year reflection",
];

const SESSION_KEY = `listinglift_session_${PRODUCT_VARIANT}_v1`;

export function App() {
  const sessionFileInputRef = useRef(null);
  const [logoMissing, setLogoMissing] = useState(false);
  const [seed, setSeed] = useState("");
  const [reverseIntelKeyword, setReverseIntelKeyword] = useState("");
  const [goldOnly, setGoldOnly] = useState(false);
  const [storeLevel, setStoreLevel] = useState(STORE_LEVELS[0].value);
  const [winnableOnly, setWinnableOnly] = useState(true);
  const [beginnerMode, setBeginnerMode] = useState(true);
  const [startHereOnly, setStartHereOnly] = useState(false);
  const [tptStageConfirmed, setTptStageConfirmed] = useState(false);
  const [keywordIntent, setKeywordIntent] = useState("idea");
  const [keywordsLoading, setKeywordsLoading] = useState(false);
  const [keywordsError, setKeywordsError] = useState("");
  const [keywordItems, setKeywordItems] = useState([]);

  const [reverseIntelLoading, setReverseIntelLoading] = useState(false);
  const [reverseIntelError, setReverseIntelError] = useState("");
  const [reverseIntelResult, setReverseIntelResult] = useState(null);

  const [form, setForm] = useState({
    platform: PLATFORM_OPTIONS[0].value,
    niche: NICHES[0],
    buyerType: BUYER_TYPES[0],
    productStage: PRODUCT_STAGES[2],
    sellerConfidence: SELLER_CONFIDENCE_LEVELS[0],
    productDescription: "",
  });
  const [listingLoading, setListingLoading] = useState(false);
  const [listingError, setListingError] = useState("");
  const [listing, setListing] = useState(null);

  const [auditForm, setAuditForm] = useState({
    title: "",
    tags: "",
    description: "",
  });
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState("");
  const [auditResult, setAuditResult] = useState(null);
  const [sessionNote, setSessionNote] = useState("");

  const descriptionChars = form.productDescription.length;
  const descriptionReady = descriptionChars >= 20;
  const activePlatform = form.platform;
  const activePlatformLabel =
    PLATFORM_OPTIONS.find((item) => item.value === activePlatform)?.label || "Selected platform";
  const activeCapabilities = PLATFORM_CAPABILITIES[activePlatform] || { keywords: false, audit: false };
  const activeLimits = PLATFORM_LIMITS[activePlatform] || { titleLimit: 80, tagLimit: 20 };
  const isSingleStoreProduct = PLATFORM_OPTIONS.length === 1;
  const enabledPlatformsLabel = PLATFORM_OPTIONS.map((item) => item.label).join(", ");
  const effectiveStoreLevel = beginnerMode ? "new_store" : storeLevel;
  const effectiveWinnableOnly = beginnerMode ? true : winnableOnly;

  const seedPlaceholder = useMemo(() => {
    if (keywordIntent === "angle") {
      return "christmas social stories";
    }
    return "social stories autism";
  }, [keywordIntent]);

  const seedLabel = useMemo(() => {
    if (keywordIntent === "angle") {
      return "Theme / product topic";
    }
    return "Seed topic";
  }, [keywordIntent]);

  const titleStatus = useMemo(() => {
    if (!listing) return "muted";
    return listing.title_chars <= listing.title_limit ? "ok" : "bad";
  }, [listing]);

  const visibleKeywordItems = useMemo(() => {
    if (!startHereOnly) {
      return keywordItems;
    }
    return keywordItems.filter((item) => item.recommendation_label === "Start Here");
  }, [keywordItems, startHereOnly]);

  const startHereItems = useMemo(() => {
    return visibleKeywordItems.filter((item) => item.recommendation_label === "Start Here");
  }, [visibleKeywordItems]);

  async function onSearchKeywords(event) {
    event.preventDefault();
    if (!activeCapabilities.keywords) {
      setKeywordsError(`Niche Engine is not available in the ${activePlatformLabel} edition yet.`);
      setKeywordItems([]);
      return;
    }
    if (!seed.trim()) {
      setKeywordsError("Enter a seed topic first.");
      return;
    }

    setKeywordsLoading(true);
    setKeywordsError("");
    try {
      const response = await fetchKeywords(
        activePlatform,
        seed.trim(),
        goldOnly,
        effectiveStoreLevel,
        effectiveWinnableOnly,
      );
      setKeywordItems(response.items || []);
      setKeywordsError("");

      if (!reverseIntelKeyword.trim()) {
        setReverseIntelKeyword(seed);
      }
    } catch (error) {
      setKeywordsError(error.message || "Keyword lookup failed.");
    } finally {
      setKeywordsLoading(false);
    }
  }

  async function onRunReverseIntel() {
    if (!activeCapabilities.keywords) {
      setReverseIntelError(`Reverse intel is not available in the ${activePlatformLabel} edition yet.`);
      return;
    }

    const keyword = (reverseIntelKeyword || seed).trim();
    if (!keyword) {
      setReverseIntelError("Enter a keyword first.");
      return;
    }

    setReverseIntelLoading(true);
    setReverseIntelError("");

    try {
      const payload = await fetchReverseIntel(keyword, 18);
      setReverseIntelResult(payload);
    } catch (error) {
      setReverseIntelResult(null);
      setReverseIntelError(error.message || "Reverse intel failed.");
    } finally {
      setReverseIntelLoading(false);
    }
  }

  function onUseKeywordInDraft(phrase) {
    const marker = `Target keyword: ${phrase}`;
    setForm((old) => {
      if (old.productDescription.toLowerCase().includes(marker.toLowerCase())) {
        return old;
      }
      return {
        ...old,
        productDescription: old.productDescription.trim() ? `${marker}\n${old.productDescription}` : marker,
      };
    });
    setSessionNote(`Added "${phrase}" into your listing draft notes.`);
  }

  function onUseSuggestedTitleInDraft(title) {
    const marker = `Preferred title idea: ${title}`;
    setForm((old) => {
      if (old.productDescription.toLowerCase().includes(marker.toLowerCase())) {
        return old;
      }
      return {
        ...old,
        productDescription: old.productDescription.trim() ? `${marker}\n${old.productDescription}` : marker,
      };
    });
    setSessionNote("Added the suggested title into your listing draft notes.");
  }

  function downloadFile(fileName, text, mimeType) {
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function onExportKeywordsCsv() {
    if (!visibleKeywordItems.length) {
      return;
    }
    const rows = [
      [
        "Keyword phrase",
        "Demand",
        "Opportunity score",
        "Confidence",
        "TPT supply",
        "Avg reviews (P1)",
        "Winnable",
        "Verdict",
        "Recommendation",
        "Recommendation reason",
      ],
      ...visibleKeywordItems.map((row) => [
        row.phrase,
        row.demand_label,
        row.opportunity_score,
        keywordConfidence(row),
        row.tpt_supply_count === null ? "n/a" : String(row.tpt_supply_count),
        row.avg_top5_reviews === null ? "n/a" : String(row.avg_top5_reviews),
        row.winnable_now ? "Yes" : "No",
        row.verdict,
        row.recommendation_label,
        row.recommendation_reason,
      ]),
    ];
    const csv = rows
      .map((line) => line.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
      .join("\n");
    downloadFile("listinglift-keywords.csv", csv, "text/csv;charset=utf-8");
  }

  function onExportListingTxt() {
    if (!listing) {
      return;
    }
    const lines = [
      `Platform: ${activePlatformLabel}`,
      "",
      "TITLE",
      listing.title,
      "",
      "TAGS",
      listing.tags_limit > 0 ? listing.tags.join(", ") : "Not used on this platform",
      "",
      "OPENING LINES",
      listing.description_opener,
      "",
      "FIRST 180-CHAR PREVIEW",
      listing.description_snippet,
      "",
      "FULL LISTING DESCRIPTION",
      listing.full_description,
      "",
      "EXTRA KEYWORD IDEAS",
      ...listing.keyword_angles,
      "",
      "NEXT PRODUCT IDEAS",
      ...listing.gap_opportunities,
    ];
    downloadFile("listinglift-draft.txt", lines.join("\n"), "text/plain;charset=utf-8");
  }

  function onSaveSession() {
    try {
      const snapshot = buildSessionSnapshot();
      localStorage.setItem(SESSION_KEY, JSON.stringify(snapshot));
      setSessionNote("Session saved on this device.");
    } catch {
      setSessionNote("Could not save session on this device.");
    }
  }

  function buildSessionSnapshot() {
    return {
      seed,
      goldOnly,
      storeLevel,
      winnableOnly,
      beginnerMode,
      startHereOnly,
      tptStageConfirmed,
      keywordIntent,
      keywordItems,
      form,
      listing,
      auditForm,
      auditResult,
    };
  }

  function applySessionSnapshot(snapshot) {
    const snapshotPlatform = snapshot?.form?.platform;
    const hasSnapshotPlatform = PLATFORM_OPTIONS.some((item) => item.value === snapshotPlatform);
    setSeed(snapshot.seed || "");
    setGoldOnly(Boolean(snapshot.goldOnly));
    setBeginnerMode(snapshot.beginnerMode ?? true);
    setStartHereOnly(Boolean(snapshot.startHereOnly));
    setTptStageConfirmed(Boolean(snapshot.tptStageConfirmed));
    setKeywordIntent(snapshot.keywordIntent === "angle" ? "angle" : "idea");
    setStoreLevel(snapshot.storeLevel || STORE_LEVELS[0].value);
    setWinnableOnly(snapshot.winnableOnly ?? true);
    setKeywordItems(Array.isArray(snapshot.keywordItems) ? snapshot.keywordItems : []);
    setForm((old) => ({
      ...old,
      ...(snapshot.form || {}),
      platform: hasSnapshotPlatform ? snapshotPlatform : PLATFORM_OPTIONS[0].value,
    }));
    setListing(snapshot.listing || null);
    setAuditForm((old) => ({ ...old, ...(snapshot.auditForm || {}) }));
    setAuditResult(snapshot.auditResult || null);
  }

  function onConfirmTptStoreStage() {
    setTptStageConfirmed(true);

    if (storeLevel === "new_store") {
      setBeginnerMode(true);
      setWinnableOnly(true);
    } else {
      setBeginnerMode(false);
    }
  }

  function onChangeTptStoreStage() {
    setTptStageConfirmed(false);
  }

  function onUseSeedExample(example) {
    setSeed(example);
    setKeywordsError("");
  }

  function onDownloadSessionJson() {
    try {
      const snapshot = buildSessionSnapshot();
      const fileName = "listinglift-session.json";
      const text = JSON.stringify(snapshot, null, 2);
      downloadFile(fileName, text, "application/json;charset=utf-8");
      setSessionNote("Session JSON downloaded.");
    } catch {
      setSessionNote("Could not download session JSON.");
    }
  }

  function onPickSessionFile() {
    sessionFileInputRef.current?.click();
  }

  async function onUploadSessionJson(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const text = await file.text();
      const snapshot = JSON.parse(text);
      applySessionSnapshot(snapshot || {});
      setSessionNote("Session JSON loaded.");
    } catch {
      setSessionNote("Could not load session JSON.");
    } finally {
      event.target.value = "";
    }
  }

  function onLoadSession() {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      if (!raw) {
        setSessionNote("No saved session found yet.");
        return;
      }
      const snapshot = JSON.parse(raw);
      applySessionSnapshot(snapshot || {});
      setSessionNote("Session loaded.");
    } catch {
      setSessionNote("Could not load saved session.");
    }
  }

  async function onAuditListing(event) {
    event.preventDefault();
    if (!activeCapabilities.audit) {
      setAuditError(`Listing Audit is not available in the ${activePlatformLabel} edition yet.`);
      setAuditResult(null);
      return;
    }
    if (auditForm.title.trim().length < 5 || auditForm.description.trim().length < 20) {
      setAuditError("Add a title and description before running audit.");
      return;
    }

    setAuditLoading(true);
    setAuditError("");
    try {
      const payload = await auditListing({
        ...auditForm,
        platform: activePlatform,
        tags: activeLimits.tagLimit > 0 ? auditForm.tags : "",
      });
      setAuditResult(payload);
    } catch (error) {
      setAuditError(error.message);
    } finally {
      setAuditLoading(false);
    }
  }

  async function onGenerateListing(event) {
    event.preventDefault();
    if (!descriptionReady) {
      setListingError("Product description must be at least 20 characters.");
      return;
    }

    setListingLoading(true);
    setListingError("");
    try {
      const payload = await generateListing(form);
      setListing(payload);
    } catch (error) {
      setListingError(error.message);
    } finally {
      setListingLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand-wrap">
          {logoMissing ? (
            <div className="brand-mark">EP</div>
          ) : (
            <img
              className="brand-logo"
              src="/easyprep-logo.png"
              alt="EasyPrep logo"
              onError={() => setLogoMissing(true)}
            />
          )}
          <div>
            <h1>ListingLift</h1>
            <p>by EasyPrep</p>
            <p className="brand-subline">From the makers of PackReady</p>
          </div>
        </div>
        <div className="header-controls">
          <input
            ref={sessionFileInputRef}
            type="file"
            accept="application/json,.json"
            onChange={onUploadSessionJson}
            style={{ display: "none" }}
          />
          <details className="session-menu">
            <summary className="ghost-btn toolbar-btn session-summary">Session</summary>
            <div className="session-menu-panel">
              <button className="ghost-btn toolbar-btn" onClick={onSaveSession} type="button">
                Save Session
              </button>
              <button className="ghost-btn toolbar-btn" onClick={onLoadSession} type="button">
                Load Session
              </button>
              <button className="ghost-btn toolbar-btn" onClick={onDownloadSessionJson} type="button">
                Download Session
              </button>
              <button className="ghost-btn toolbar-btn" onClick={onPickSessionFile} type="button">
                Upload Session
              </button>
            </div>
          </details>
          <select
            className="store-level-select"
            value={form.platform}
            onChange={(event) => setForm((old) => ({ ...old, platform: event.target.value }))}
            disabled={isSingleStoreProduct}
          >
            {PLATFORM_OPTIONS.map((platform) => (
              <option key={platform.value} value={platform.value}>
                {platform.label}
              </option>
            ))}
          </select>
          <select
            className="store-level-select"
            value={effectiveStoreLevel}
            onChange={(event) => setStoreLevel(event.target.value)}
            disabled={activePlatform !== "tpt" || beginnerMode}
          >
            {STORE_LEVELS.map((level) => (
              <option key={level.value} value={level.value}>
                {level.label}
              </option>
            ))}
          </select>
        </div>
      </header>

      {sessionNote ? <p className="session-note">{sessionNote}</p> : null}

      <section className="card quickstart-card">
        <div className="card-head">
          <h2>First-run checklist</h2>
          <p>Set up once, then run keyword ideas, listing draft, and quality check in a clear step-by-step flow.</p>
        </div>
        <ol className="checklist">
          <li>Use this product for: {enabledPlatformsLabel}.</li>
          <li>If using TPT, keep your current store level selected for practical competition checks.</li>
          <li>Paste your product details and generate a listing draft matched to that platform's limits.</li>
          <li>Before publishing, run Listing Audit and apply the top fixes.</li>
        </ol>
      </section>

      <main className="content-grid">
        <section className="card">
          <div className="card-head">
            <h2>Niche Engine</h2>
            <p>
              {activeCapabilities.keywords
                ? "Start here first: find high-demand, low-competition gaps you can actually win as a newer seller."
                : "Niche Engine is currently only available in the TPT edition."}
            </p>
          </div>
          <p className="module-tip">
            <strong>What to do first:</strong> Enter a broad topic, then pick a "Start Here" keyword before building your product.
          </p>

          {!activeCapabilities.keywords ? (
            <div className="notice">
              Niche Engine is not included in this edition yet. You can still generate listings for
              {" "}
              {activePlatformLabel}.
            </div>
          ) : null}

          {activePlatform === "tpt" && activeCapabilities.keywords ? (
            <div className="onboarding-card">
              <div className="onboarding-head">
                <h3>1) Tell us your TPT store stage</h3>
                <p>This changes what we label as “Start Here” so you avoid competing with huge stores.</p>
              </div>
              <div className="onboarding-controls">
                <select
                  className="input"
                  value={storeLevel}
                  onChange={(event) => setStoreLevel(event.target.value)}
                  disabled={tptStageConfirmed}
                >
                  {STORE_LEVELS.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
                {!tptStageConfirmed ? (
                  <button className="primary-btn" type="button" onClick={onConfirmTptStoreStage}>
                    Confirm store stage
                  </button>
                ) : (
                  <button className="ghost-btn" type="button" onClick={onChangeTptStoreStage}>
                    Change
                  </button>
                )}
              </div>
              {!tptStageConfirmed ? (
                <p className="helper-copy">Once confirmed, we’ll keep your recommendations aligned to your current authority level.</p>
              ) : null}
            </div>
          ) : null}

          {activeCapabilities.keywords ? (
            <div className="intent-card">
              <div className="onboarding-head">
                <h3>2) What are you working on today?</h3>
                <p>Same engine — we just tailor the examples and guidance.</p>
              </div>
              <div className="intent-buttons">
                <button
                  className={keywordIntent === "idea" ? "primary-btn" : "ghost-btn"}
                  type="button"
                  onClick={() => setKeywordIntent("idea")}
                >
                  I need an idea (what should I sell?)
                </button>
                <button
                  className={keywordIntent === "angle" ? "primary-btn" : "ghost-btn"}
                  type="button"
                  onClick={() => setKeywordIntent("angle")}
                >
                  I have a theme/product (best angle)
                </button>
              </div>
            </div>
          ) : null}

          <form onSubmit={onSearchKeywords} className="stack">
            <label className="label" htmlFor="seed">
              {seedLabel}
            </label>
            <input
              id="seed"
              className="input"
              value={seed}
              onChange={(event) => setSeed(event.target.value)}
              placeholder={seedPlaceholder}
            />

            <div className="seed-chips">
              {(keywordIntent === "angle" ? ANGLE_SEED_EXAMPLES : IDEA_SEED_EXAMPLES).map((example) => (
                <button
                  key={example}
                  className="chip-btn"
                  type="button"
                  onClick={() => onUseSeedExample(example)}
                >
                  {example}
                </button>
              ))}
            </div>

            <label className="check-row">
              <input
                type="checkbox"
                checked={startHereOnly}
                onChange={(event) => setStartHereOnly(event.target.checked)}
                disabled={!activeCapabilities.keywords}
              />
              Start Here only
            </label>

            <details className="advanced" open={false}>
              <summary className="advanced-summary">Advanced options</summary>

              <div className="advanced-panel">
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={goldOnly}
                    onChange={(event) => setGoldOnly(event.target.checked)}
                    disabled={!activeCapabilities.keywords}
                  />
                  Show best opportunities only
                </label>

                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={beginnerMode}
                    onChange={(event) => {
                      const enabled = event.target.checked;
                      setBeginnerMode(enabled);
                      if (enabled) {
                        setStoreLevel("new_store");
                        setWinnableOnly(true);
                      }
                    }}
                    disabled={!activeCapabilities.keywords}
                  />
                  Beginner Mode (0 reviews / 0 sales)
                </label>

                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={effectiveWinnableOnly}
                    onChange={(event) => setWinnableOnly(event.target.checked)}
                    disabled={!activeCapabilities.keywords || beginnerMode}
                  />
                  Realistic for my store right now
                </label>
              </div>
            </details>

            {beginnerMode && activeCapabilities.keywords ? (
              <p className="helper-copy">
                Beginner Mode keeps results focused on lower-competition opportunities for brand-new stores.
              </p>
            ) : null}

            <button className="primary-btn" disabled={keywordsLoading || !activeCapabilities.keywords} type="submit">
              {keywordsLoading ? "Searching..." : "Find Keywords"}
            </button>
          </form>

          {keywordsError ? <p className="error">{keywordsError}</p> : null}

          {!visibleKeywordItems.length && !keywordsLoading && !keywordsError && activeCapabilities.keywords ? (
            <div className="empty-hint">
              <h3>Start with a broad topic, then pick one “Start Here” keyword.</h3>
              <p>Tip: click an example above, then press “Find Keywords”.</p>
            </div>
          ) : null}

          {visibleKeywordItems.length ? (
            <div className="output-stack keyword-guidance-stack">
              {(startHereItems.length ? startHereItems : visibleKeywordItems).slice(0, 3).map((row) => (
                <div className="output-block" key={`${row.phrase}-guidance`}>
                  <div className="split-row">
                    <div>
                      <h3>{row.phrase}</h3>
                      {formatSourceHits(row.source_hits) ? (
                        <p className="source-note">{formatSourceHits(row.source_hits)}</p>
                      ) : null}
                    </div>
                    <div className="badge-row">
                      <ConfidenceBadge level={keywordConfidence(row)} />
                      <RecommendationBadge label={row.recommendation_label} />
                    </div>
                  </div>
                  <p className="helper-copy">{row.recommendation_reason}</p>
                  <ul>
                    {(row.next_steps || []).map((step) => (
                      <li key={`${row.phrase}-${step}`}>{step}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : null}

          {activeCapabilities.keywords ? (
            <section className="intel-card">
              <div className="card-head">
                <h3>Reverse Seller Intel (v0)</h3>
                <p>See how top listings phrase this keyword, then borrow the winning angle.</p>
              </div>

              <div className="intel-controls">
                <input
                  className="input"
                  value={reverseIntelKeyword}
                  onChange={(event) => setReverseIntelKeyword(event.target.value)}
                  placeholder="Example: social story autism"
                />
                <button className="primary-btn" type="button" onClick={onRunReverseIntel} disabled={reverseIntelLoading}>
                  {reverseIntelLoading ? "Scanning..." : "Scan top listings"}
                </button>
              </div>

              {reverseIntelError ? <p className="error">{reverseIntelError}</p> : null}

              {reverseIntelResult ? (
                <div className="intel-output">
                  {reverseIntelResult.angles?.length ? (
                    <div className="output-block">
                      <h4>Suggested angles</h4>
                      <ul>
                        {reverseIntelResult.angles.map((angle) => (
                          <li key={angle}>{angle}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  {reverseIntelResult.recurring_phrases?.length ? (
                    <div className="output-block">
                      <h4>Recurring phrases</h4>
                      <div className="phrase-chips">
                        {reverseIntelResult.recurring_phrases.map((phrase) => (
                          <span className="phrase-chip" key={phrase}>
                            {phrase}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {reverseIntelResult.listings?.length ? (
                    <div className="output-block">
                      <h4>Top listing titles (sample)</h4>
                      <ol className="listing-ol">
                        {reverseIntelResult.listings.slice(0, 10).map((item) => (
                          <li key={`${item.rank}-${item.title}`}>
                            <div className="intel-title-row">
                              <span>{item.title}</span>
                              <CopyButton value={item.title} className="inline-btn" />
                            </div>
                          </li>
                        ))}
                      </ol>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </section>
          ) : null}

          <details className="all-results" open={false}>
            <summary className="all-results-summary">All keyword results</summary>

            <div className="table-head">
              <div>
                <p className="helper-copy">Click a keyword to copy it or send it directly into your listing draft notes.</p>
              </div>
              <div className="section-actions">
                <button
                  className="ghost-btn"
                  type="button"
                  onClick={onExportKeywordsCsv}
                  disabled={!visibleKeywordItems.length}
                >
                  Export CSV
                </button>
              </div>
            </div>

            {visibleKeywordItems.length ? (
              <p className="sort-note">Sorted by Opportunity Score (highest to lowest).</p>
            ) : null}

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Keyword phrase</th>
                    <th>Demand</th>
                    <th>Opportunity</th>
                    <th>Confidence</th>
                    <th>TPT supply</th>
                    <th>Avg reviews (P1)</th>
                    <th>Winnable</th>
                    <th>Verdict</th>
                    <th>Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleKeywordItems.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="empty-cell">
                        No keyword ideas yet. Enter a seed topic above.
                      </td>
                    </tr>
                  ) : (
                    visibleKeywordItems.map((row) => (
                      <tr key={row.phrase}>
                        <td>
                          <div className="row-keyword">{row.phrase}</div>
                          {formatSourceHits(row.source_hits) ? (
                            <div className="row-subline">{formatSourceHits(row.source_hits)}</div>
                          ) : null}
                          <div className="keyword-actions">
                            <CopyButton value={row.phrase} className="inline-btn" />
                            <button
                              className="ghost-btn inline-btn"
                              onClick={() => onUseKeywordInDraft(row.phrase)}
                              type="button"
                            >
                              Use in draft
                            </button>
                          </div>
                        </td>
                        <td>{row.demand_label}</td>
                        <td>
                          <span className="opportunity-pill">{row.opportunity_score}</span>
                        </td>
                        <td>
                          <ConfidenceBadge level={keywordConfidence(row)} />
                        </td>
                        <td>{row.tpt_supply_count === null ? "n/a" : row.tpt_supply_count}</td>
                        <td>{row.avg_top5_reviews === null ? "n/a" : row.avg_top5_reviews}</td>
                        <td>{row.winnable_now ? "Yes" : "No"}</td>
                        <td>
                          <VerdictBadge verdict={row.verdict} />
                        </td>
                        <td>
                          <RecommendationBadge label={row.recommendation_label} />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </details>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>Listing draft builder</h2>
            <p>Answer a few questions and generate a clean draft fitted to your selected platform.</p>
          </div>
          <p className="module-tip">
            <strong>What to do first:</strong> Choose your store, then paste your product details in plain language.
          </p>

          <p className="helper-copy">
            Your draft will automatically follow the title and tag limits for {activePlatformLabel}.
          </p>

          <form onSubmit={onGenerateListing} className="stack">
            <label className="label" htmlFor="platform">
              Which store are you listing on?
            </label>
            {isSingleStoreProduct ? (
              <div className="notice">{activePlatformLabel} edition is locked to this store.</div>
            ) : (
              <select
                id="platform"
                className="input"
                value={form.platform}
                onChange={(event) => setForm((old) => ({ ...old, platform: event.target.value }))}
              >
                {PLATFORM_OPTIONS.map((platform) => (
                  <option value={platform.value} key={platform.value}>
                    {platform.label}
                  </option>
                ))}
              </select>
            )}

            <label className="label" htmlFor="niche">
              Niche
            </label>
            <select
              id="niche"
              className="input"
              value={form.niche}
              onChange={(event) => setForm((old) => ({ ...old, niche: event.target.value }))}
            >
              {NICHES.map((item) => (
                <option value={item} key={item}>
                  {item}
                </option>
              ))}
            </select>

            <label className="label" htmlFor="buyerType">
              Target buyer
            </label>
            <select
              id="buyerType"
              className="input"
              value={form.buyerType}
              onChange={(event) => setForm((old) => ({ ...old, buyerType: event.target.value }))}
            >
              {BUYER_TYPES.map((item) => (
                <option value={item} key={item}>
                  {item}
                </option>
              ))}
            </select>

            <label className="label" htmlFor="productStage">
              Where are you up to right now?
            </label>
            <select
              id="productStage"
              className="input"
              value={form.productStage}
              onChange={(event) => setForm((old) => ({ ...old, productStage: event.target.value }))}
            >
              {PRODUCT_STAGES.map((item) => (
                <option value={item} key={item}>
                  {item}
                </option>
              ))}
            </select>

            <label className="label" htmlFor="sellerConfidence">
              How confident are you with listings?
            </label>
            <select
              id="sellerConfidence"
              className="input"
              value={form.sellerConfidence}
              onChange={(event) => setForm((old) => ({ ...old, sellerConfidence: event.target.value }))}
            >
              {SELLER_CONFIDENCE_LEVELS.map((item) => (
                <option value={item} key={item}>
                  {item}
                </option>
              ))}
            </select>

            <div className="split-row">
              <label className="label" htmlFor="description">
                Product description
              </label>
              <span className={descriptionReady ? "counter-ok" : "counter-warn"}>{descriptionChars} chars</span>
            </div>
            <textarea
              id="description"
              className="textarea"
              value={form.productDescription}
              onChange={(event) => setForm((old) => ({ ...old, productDescription: event.target.value }))}
              placeholder="Paste your product details, target learner, and what is included..."
            />

            <button className="primary-btn" disabled={listingLoading || !descriptionReady} type="submit">
              {listingLoading ? "Generating..." : "Generate Listing Draft"}
            </button>
          </form>

          {listingError ? <p className="error">{listingError}</p> : null}

          {listing ? (
            <div className="output-stack">
              <div className="section-actions">
                <button className="ghost-btn inline-btn" onClick={onExportListingTxt} type="button">
                  Export Listing TXT
                </button>
              </div>
              <div className="output-block">
                <div className="split-row">
                  <h3>Ready-to-paste title</h3>
                  <span className={`counter-${titleStatus}`}>
                    {listing.title_chars}/{listing.title_limit}
                  </span>
                </div>
                <p>{listing.title}</p>
                <CopyButton value={listing.title} className="inline-btn" />
              </div>

              {listing.tags_limit > 0 ? (
                <div className="output-block">
                  <div className="split-row">
                    <h3>Ready-to-paste tags</h3>
                    <span className="counter-ok">
                      {listing.tags_count}/{listing.tags_limit}
                    </span>
                  </div>
                  <p>{listing.tags.join(", ")}</p>
                  <CopyButton value={listing.tags.join(", ")} className="inline-btn" />
                </div>
              ) : (
                <div className="output-block">
                  <h3>Tags</h3>
                  <p>This platform does not use tags. Focus on title + description quality.</p>
                </div>
              )}

              <div className="output-block">
                <h3>Opening lines</h3>
                <p>{listing.description_opener}</p>
                <CopyButton value={listing.description_opener} className="inline-btn" />
              </div>

              <div className="output-block">
                <h3>First 180-character preview</h3>
                <p>{listing.description_snippet}</p>
                <CopyButton value={listing.description_snippet} className="inline-btn" />
              </div>

              <div className="output-block">
                <h3>Full listing description</h3>
                <p>{listing.full_description}</p>
                <CopyButton value={listing.full_description} className="inline-btn" />
              </div>

              <div className="output-block">
                <h3>Extra keyword ideas</h3>
                <ul>
                  {listing.keyword_angles.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="output-block">
                <h3>Next product ideas</h3>
                <ul>
                  {listing.gap_opportunities.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </section>
      </main>

      <section className="card audit-card">
        <div className="card-head">
          <h2>Listing Audit</h2>
          <p>Score your current listing and get clear next-step fixes for supported platforms.</p>
        </div>
        <p className="module-tip">
          <strong>What to do first:</strong> Paste your current listing as-is. You will get simple, high-impact fixes.
        </p>

        {!activeCapabilities.audit ? (
          <div className="notice">
            Listing Audit is not included in the {activePlatformLabel} edition yet.
          </div>
        ) : null}

        <form onSubmit={onAuditListing} className="stack">
          <label className="label" htmlFor="auditTitle">
            Current title
          </label>
          <input
            id="auditTitle"
            className="input"
            value={auditForm.title}
            onChange={(event) => setAuditForm((old) => ({ ...old, title: event.target.value }))}
            placeholder={`Paste your current ${activePlatformLabel} title`}
          />

          {activeLimits.tagLimit > 0 ? (
            <>
              <label className="label" htmlFor="auditTags">
                Current tags (comma separated)
              </label>
              <input
                id="auditTags"
                className="input"
                value={auditForm.tags}
                onChange={(event) => setAuditForm((old) => ({ ...old, tags: event.target.value }))}
                placeholder="social stories autism, special education, ..."
              />
            </>
          ) : (
            <div className="notice">Tags are not used for this platform in ListingLift.</div>
          )}

          <label className="label" htmlFor="auditDescription">
            Current description
          </label>
          <textarea
            id="auditDescription"
            className="textarea"
            value={auditForm.description}
            onChange={(event) => setAuditForm((old) => ({ ...old, description: event.target.value }))}
            placeholder={`Paste your current ${activePlatformLabel} listing description`}
          />

          <button className="primary-btn" disabled={auditLoading || !activeCapabilities.audit} type="submit">
            {auditLoading ? "Auditing..." : "Run Listing Audit"}
          </button>
        </form>

        {auditError ? <p className="error">{auditError}</p> : null}

        {auditResult ? (
          <div className="output-stack">
            <div className="output-block">
              <div className="split-row">
                <h3>Overall score</h3>
                <span className="counter-ok">{auditResult.score_total}/100</span>
              </div>
            </div>
            <div className="output-block">
              <h3>Title improvement preview</h3>
              <p>
                <strong>Current title:</strong> {auditForm.title}
              </p>
              <p>
                <strong>Suggested title:</strong> {auditResult.suggested_title}
              </p>
              <p className="helper-copy">{auditResult.suggested_title_reason}</p>
              <div className="section-actions">
                <CopyButton value={auditResult.suggested_title} className="inline-btn" />
                <button
                  className="ghost-btn inline-btn"
                  onClick={() => onUseSuggestedTitleInDraft(auditResult.suggested_title)}
                  type="button"
                >
                  Use in listing draft
                </button>
              </div>
            </div>
            <div className="output-block">
              <h3>Score breakdown</h3>
              <ul>
                <li>Title: {auditResult.title_score}/25</li>
                <li>Description: {auditResult.description_score}/25</li>
                <li>Tags: {auditResult.tags_score}/25</li>
                <li>SEO coverage: {auditResult.seo_coverage_score}/25</li>
              </ul>
            </div>
            <div className="output-block">
              <h3>Best next fixes</h3>
              <ul>
                {auditResult.top_fixes.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="output-block empty-hint">
            <h3>No audit score yet</h3>
            <p>Paste your current title, tags, and description, then click "Run Listing Audit".</p>
          </div>
        )}
      </section>
    </div>
  );
}
