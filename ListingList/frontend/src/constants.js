export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const PLATFORM_CATALOG = [
  { value: "tpt", label: "Teachers Pay Teachers (TPT)" },
  { value: "etsy", label: "Etsy" },
  { value: "gumroad", label: "Gumroad" },
];

const PRODUCT_VARIANT_MAP = {
  multi: ["tpt", "etsy", "gumroad"],
  tpt: ["tpt"],
  etsy: ["etsy"],
  gumroad: ["gumroad"],
};

export const PRODUCT_VARIANT = (import.meta.env.VITE_PRODUCT_VARIANT || "multi").toLowerCase();

const enabledPlatformValues = PRODUCT_VARIANT_MAP[PRODUCT_VARIANT] || PRODUCT_VARIANT_MAP.multi;

export const PLATFORM_OPTIONS = PLATFORM_CATALOG.filter((item) => enabledPlatformValues.includes(item.value));

export const PLATFORM_CAPABILITIES = {
  tpt: { keywords: true, audit: true },
  etsy: { keywords: false, audit: true },
  gumroad: { keywords: false, audit: true },
};

export const PLATFORM_LIMITS = {
  tpt: { titleLimit: 80, tagLimit: 20 },
  etsy: { titleLimit: 140, tagLimit: 13 },
  gumroad: { titleLimit: 140, tagLimit: 0 },
};

export const NICHES = [
  "Special Education",
  "AAC / Communication",
  "Social Stories",
  "Adapted Literacy",
  "Autism Support",
  "Intellectual Disability",
  "Behaviour Support",
  "Morning Work",
  "ELA",
  "Math",
  "Science",
  "Social Studies",
  "Art",
  "Music",
  "Physical Education",
  "Seasonal / Holiday",
  "Back to School",
  "TPT Seller Tools",
  "General / All Subjects",
];

export const BUYER_TYPES = [
  "SPED teacher",
  "General classroom teacher",
  "Interventionist",
  "Homeschool parent",
  "School district buyer",
  "SLP",
];

export const STORE_LEVELS = [
  { value: "new_store", label: "New store (0-5 reviews)" },
  { value: "growing", label: "Growing (6-25 reviews)" },
  { value: "established", label: "Established (26-100 reviews)" },
  { value: "authority", label: "Authority (100+ reviews)" },
];

export const PRODUCT_STAGES = [
  "I only have an idea",
  "Draft product in progress",
  "Product is finished",
  "I already listed it and want to improve it",
];

export const SELLER_CONFIDENCE_LEVELS = [
  "Beginner - I need step-by-step help",
  "Comfortable - I understand listing basics",
  "Advanced - I optimize listings regularly",
];
