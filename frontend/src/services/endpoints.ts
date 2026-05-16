export const endpoints = {
  auth: {
    login: "/api/v1/auth/login",
    register: "/api/v1/auth/register",
    me: "/api/v1/auth/me",
    tokenLogin: (verify: string) => `/api/v1/auth/token2-login?verify=${encodeURIComponent(verify)}`,
    emailVerify: "/api/v1/auth/email-verify",
    forget: "/api/v1/auth/forget",
  },
  common: {
    config: "/api/v1/common/config",
  },
  user: {
    info: "/api/v1/user/info",
    profile: "/api/v1/user/profile",
    changePassword: "/api/v1/user/change-password",
    quickLoginUrl: "/api/v1/user/quick-login-url",
    unbindTelegram: "/api/v1/user/unbind-telegram",
    subscribe: "/api/v1/user/subscribe",
    servers: "/api/v1/user/servers",
    stats: "/api/v1/user/stats",
    trafficLogs: (limit = 8) => `/api/v1/user/traffic-logs?limit=${limit}`,
    resetSecurity: "/api/v1/user/reset-security",
  },
  comm: {
    stripePublicKey: "/api/v1/comm/stripe-public-key",
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
  tickets: {
    list: (offset = 0, limit = 50) => `/api/v1/tickets?offset=${offset}&limit=${limit}`,
    detail: (ticketId: number) => `/api/v1/tickets/${ticketId}`,
    create: "/api/v1/tickets",
    reply: (ticketId: number) => `/api/v1/tickets/${ticketId}/reply`,
    close: (ticketId: number) => `/api/v1/tickets/${ticketId}/close`,
    withdraw: "/api/v1/tickets/withdraw",
  },
  invite: {
    overview: "/api/v1/invite",
    createCode: "/api/v1/invite/codes",
    commissionLogs: (offset = 0, limit = 50) => `/api/v1/invite/commission-logs?offset=${offset}&limit=${limit}`,
    transferCommission: "/api/v1/invite/commission/transfer",
  },
} as const;
