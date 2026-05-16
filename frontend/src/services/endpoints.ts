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
  plans: {
    list: "/api/v1/plans",
    detail: (planId: number) => `/api/v1/plans/${planId}`,
  },
  orders: {
    list: (status?: number) => `/api/v1/orders${status === undefined ? "" : `?status=${status}`}`,
    detail: (tradeNo: string) => `/api/v1/orders/detail?trade_no=${encodeURIComponent(tradeNo)}`,
    create: "/api/v1/orders",
    checkout: "/api/v1/orders/checkout",
    check: (tradeNo: string) => `/api/v1/orders/check?trade_no=${encodeURIComponent(tradeNo)}`,
    cancel: "/api/v1/orders/cancel",
  },
  paymentMethods: {
    list: "/api/v1/payment-methods",
  },
} as const;
