"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export const SPA_NAVIGATION_EVENT = "pyboard:navigate";

export function useSpaPathname(): string {
  const nextPathname = usePathname();
  const [pathname, setPathname] = useState(() => normalizePathname(nextPathname));

  useEffect(() => {
    setPathname(normalizePathname(nextPathname));
  }, [nextPathname]);

  useEffect(() => {
    const syncPathname = () => setPathname(normalizePathname(window.location.pathname));

    window.addEventListener("popstate", syncPathname);
    window.addEventListener(SPA_NAVIGATION_EVENT, syncPathname);
    return () => {
      window.removeEventListener("popstate", syncPathname);
      window.removeEventListener(SPA_NAVIGATION_EVENT, syncPathname);
    };
  }, []);

  return pathname;
}

export function navigateSpa(href: string): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const nextUrl = toSameOriginPath(href);
  if (!nextUrl) {
    return false;
  }

  const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (currentUrl !== nextUrl) {
    window.history.pushState(null, "", nextUrl);
    window.scrollTo(0, 0);
  }

  window.dispatchEvent(new CustomEvent(SPA_NAVIGATION_EVENT));
  return true;
}

function toSameOriginPath(href: string): string | null {
  if (!href || href === "#") {
    return null;
  }

  const url = new URL(href, window.location.origin);
  if (url.origin !== window.location.origin) {
    return null;
  }

  return `${url.pathname}${url.search}${url.hash}`;
}

function normalizePathname(pathname: string | null): string {
  if (!pathname || pathname === "/") {
    return "/";
  }
  return pathname.replace(/\/+$/, "");
}
