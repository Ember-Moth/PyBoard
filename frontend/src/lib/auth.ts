const TOKEN_KEY = "v2board_auth_token";
const SESSION_TOKEN_KEY = "v2board_session_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY) || window.sessionStorage.getItem(SESSION_TOKEN_KEY);
}

export function setAuthToken(token: string, persist = true): void {
  clearAuthToken();
  if (persist) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.sessionStorage.setItem(SESSION_TOKEN_KEY, token);
  }
}

export function clearAuthToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(SESSION_TOKEN_KEY);
}
