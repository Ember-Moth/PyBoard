"use client";

import { Alert, Box } from "@mui/material";
import { useEffect, useRef } from "react";

type TurnstileInstance = {
  render: (element: HTMLElement, options: Record<string, unknown>) => string;
  remove: (widgetId: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileInstance;
  }
}

type Props = {
  siteKey?: string;
  onVerify: (token: string) => void;
};

export default function TurnstileWidget({ siteKey, onVerify }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!siteKey || !containerRef.current) {
      return;
    }

    let cancelled = false;

    const renderWidget = () => {
      if (cancelled || !window.turnstile || !containerRef.current || widgetIdRef.current) {
        return;
      }
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        callback: onVerify,
      });
    };

    const existing = document.getElementById("turnstile-script");
    if (existing) {
      renderWidget();
    } else {
      const script = document.createElement("script");
      script.id = "turnstile-script";
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.onload = renderWidget;
      document.head.appendChild(script);
    }

    return () => {
      cancelled = true;
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };
  }, [siteKey, onVerify]);

  if (!siteKey) {
    return <Alert severity="warning">Turnstile Site Key 未配置</Alert>;
  }

  return <Box ref={containerRef} />;
}
