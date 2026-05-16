export const endpoints = {
  auth: {
    login: "/api/v1/auth/login",
    register: "/api/v1/auth/register",
    me: "/api/v1/auth/me",
    tokenLogin: (verify: string) => `/api/v1/auth/token2-login?verify=${encodeURIComponent(verify)}`,
    emailVerify: "/api/v1/auth/email-verify",
    forget: "/api/v1/auth/forget",
  },
  guest: {
    config: "/api/v1/guest/comm/config",
  },
  user: {
    info: "/api/v1/user/info",
    subscribe: "/api/v1/user/subscribe",
    servers: "/api/v1/user/servers",
    stats: "/api/v1/user/stats",
    trafficLogs: (limit = 8) => `/api/v1/user/traffic-logs?limit=${limit}`,
    resetSecurity: "/api/v1/user/reset-security",
  },
  comm: {
    config: "/api/v1/comm/config",
  },
  notices: {
    list: (page = 1, size = 5) => `/api/v1/notices?page=${page}&size=${size}`,
  },
} as const;
