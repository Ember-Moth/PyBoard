import type { FooterConfig, FooterItemConfig, RuntimeConfig } from "@/types/config";

const CONFIG_PATH = "/config.json";
const ENV_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export const DEFAULT_RUNTIME_CONFIG: RuntimeConfig = {
  apiBaseUrl: normalizeApiBaseUrl(ENV_API_BASE_URL),
  footer: {},
};

let runtimeConfigPromise: Promise<RuntimeConfig> | null = null;

export function getRuntimeConfig(): Promise<RuntimeConfig> {
  runtimeConfigPromise ??= loadRuntimeConfig();
  return runtimeConfigPromise;
}

export async function getApiBaseUrl(): Promise<string> {
  const config = await getRuntimeConfig();
  return normalizeApiBaseUrl(config.apiBaseUrl || ENV_API_BASE_URL);
}

async function loadRuntimeConfig(): Promise<RuntimeConfig> {
  try {
    const response = await fetch(CONFIG_PATH, { cache: "no-store" });
    if (!response.ok) {
      return DEFAULT_RUNTIME_CONFIG;
    }
    return normalizeRuntimeConfig(await response.json());
  } catch {
    return DEFAULT_RUNTIME_CONFIG;
  }
}

function normalizeRuntimeConfig(payload: unknown): RuntimeConfig {
  if (!isRecord(payload)) {
    return DEFAULT_RUNTIME_CONFIG;
  }

  const apiBaseUrl =
    readString(payload.apiBaseUrl) || readString(payload.api_base_url) || DEFAULT_RUNTIME_CONFIG.apiBaseUrl;

  return {
    apiBaseUrl: normalizeApiBaseUrl(apiBaseUrl),
    footer: normalizeFooterConfig(payload.footer),
  };
}

function normalizeFooterConfig(value: unknown): FooterConfig {
  if (!isRecord(value)) {
    return {};
  }

  return {
    description: readString(value.description),
    copyright: readString(value.copyright),
    seoKeywords: normalizeStringList(value.seoKeywords ?? value.seo_keywords),
    links: normalizeFooterItems(value.links),
    contacts: normalizeFooterItems(value.contacts),
  };
}

function normalizeFooterItems(value: unknown): FooterItemConfig[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.reduce<FooterItemConfig[]>((items, item) => {
    if (!isRecord(item)) {
      return items;
    }

    const label = readString(item.label);
    const href = readString(item.href);
    const text = readString(item.text);
    if (!label || (!href && !text)) {
      return items;
    }

    items.push({ label, href, text });
    return items;
  }, []);
}

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.map((item) => readString(item)).filter((item) => item.length > 0);
}

function readString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeApiBaseUrl(value: string | undefined): string {
  return value?.trim().replace(/\/+$/, "") || "";
}
