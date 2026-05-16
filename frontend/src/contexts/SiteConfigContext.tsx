"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getCommonConfig } from "@/services/common.service";
import { DEFAULT_RUNTIME_CONFIG, getRuntimeConfig } from "@/services/runtime-config.service";
import type { CommonConfig } from "@/types/api";
import type { FooterConfig, RuntimeConfig } from "@/types/config";

const DEFAULT_APP_NAME = "PyBoard";
const DEFAULT_APP_DESCRIPTION = "PyBoard panel backend.";

type SiteConfigContextValue = {
  config: CommonConfig;
  runtimeConfig: RuntimeConfig;
  footer: FooterConfig;
  loading: boolean;
  appName: string;
  appDescription: string;
  appUrl: string;
  logo: string;
  currency: string;
  currencySymbol: string;
  emailWhitelistSuffix: string[];
  emailVerifyEnabled: boolean;
  inviteRequired: boolean;
  registrationClosed: boolean;
  tosUrl: string;
  turnstileEnabled: boolean;
  turnstileSiteKey: string;
  refresh: () => Promise<void>;
};

const defaultContext: SiteConfigContextValue = {
  config: {},
  runtimeConfig: DEFAULT_RUNTIME_CONFIG,
  footer: {},
  loading: false,
  appName: DEFAULT_APP_NAME,
  appDescription: DEFAULT_APP_DESCRIPTION,
  appUrl: "",
  logo: "",
  currency: "CNY",
  currencySymbol: "¥",
  emailWhitelistSuffix: [],
  emailVerifyEnabled: false,
  inviteRequired: false,
  registrationClosed: false,
  tosUrl: "",
  turnstileEnabled: false,
  turnstileSiteKey: "",
  refresh: async () => undefined,
};

const SiteConfigContext = createContext<SiteConfigContextValue>(defaultContext);

export function SiteConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<CommonConfig>({});
  const [runtimeConfig, setRuntimeConfig] = useState<RuntimeConfig>(DEFAULT_RUNTIME_CONFIG);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [nextRuntimeConfig, nextCommonConfig] = await Promise.allSettled([getRuntimeConfig(), getCommonConfig()]);
      setRuntimeConfig(nextRuntimeConfig.status === "fulfilled" ? nextRuntimeConfig.value : DEFAULT_RUNTIME_CONFIG);
      setConfig(nextCommonConfig.status === "fulfilled" ? nextCommonConfig.value : {});
    } catch {
      setRuntimeConfig(DEFAULT_RUNTIME_CONFIG);
      setConfig({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo<SiteConfigContextValue>(() => {
    const appName = normalizeConfigText(config.app_name, DEFAULT_APP_NAME);
    const appDescription = normalizeConfigText(config.app_description, DEFAULT_APP_DESCRIPTION);
    const appUrl = config.app_url?.trim() || "";
    const logo = config.logo?.trim() || "";
    const tosUrl = config.tos_url?.trim() || "";

    return {
      config,
      runtimeConfig,
      footer: runtimeConfig.footer || {},
      loading,
      appName,
      appDescription,
      appUrl,
      logo,
      currency: normalizeConfigText(config.currency, "CNY"),
      currencySymbol: normalizeConfigText(config.currency_symbol, "¥"),
      emailWhitelistSuffix: Array.isArray(config.email_whitelist_suffix) ? config.email_whitelist_suffix : [],
      emailVerifyEnabled: Boolean(config.is_email_verify),
      inviteRequired: Boolean(config.is_invite_force),
      registrationClosed: Boolean(config.stop_register),
      tosUrl,
      turnstileEnabled: Boolean(config.is_recaptcha),
      turnstileSiteKey: config.turnstile_site_key || config.recaptcha_site_key || "",
      refresh,
    };
  }, [config, loading, refresh, runtimeConfig]);

  useEffect(() => {
    if (!value.logo) {
      return;
    }

    let link = document.querySelector<HTMLLinkElement>("link[rel='icon']");
    if (!link) {
      link = document.createElement("link");
      link.rel = "icon";
      document.head.appendChild(link);
    }
    link.href = value.logo;
  }, [value.logo]);

  return <SiteConfigContext.Provider value={value}>{children}</SiteConfigContext.Provider>;
}

export function useSiteConfig(): SiteConfigContextValue {
  return useContext(SiteConfigContext);
}

function normalizeConfigText(value: string | undefined, fallback: string): string {
  return value?.trim() || fallback;
}
