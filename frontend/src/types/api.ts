export type ApiResponse<T> = {
  code: number;
  msg: string;
  data: T | null;
};

export type TokenResponse = {
  auth_token: string;
};

export type GuestConfig = {
  tos_url?: string;
  is_email_verify?: number;
  is_invite_force?: number;
  is_recaptcha?: number;
  recaptcha_provider?: string;
  recaptcha_site_key?: string;
  turnstile_site_key?: string;
  app_description?: string;
  app_url?: string;
  logo?: string;
};

export type UserConfig = {
  is_telegram?: number;
  telegram_discuss_link?: string;
  withdraw_methods?: string[];
  withdraw_close?: number;
  currency?: string;
  currency_symbol?: string;
};

export type UserProfile = {
  email: string;
  transfer_enable: number;
  device_limit?: number | null;
  last_login_at?: number | null;
  created_at: number;
  banned: boolean;
  expired_at?: number | null;
  balance: number;
  commission_balance: number;
  plan_id?: number | null;
  uuid: string;
};

export type SubscribePlan = {
  id: number;
  name: string;
  transfer_enable: number;
  device_limit?: number | null;
  speed_limit?: number | null;
};

export type SubscribeInfo = {
  plan_id?: number | null;
  plan?: SubscribePlan | null;
  token: string;
  expired_at?: number | null;
  u: number;
  d: number;
  transfer_enable: number;
  device_limit?: number | null;
  email: string;
  uuid: string;
  alive_ip: number;
  subscribe_url: string;
  reset_day?: number | null;
  allow_new_period?: number;
};

export type TrafficLog = {
  id?: number;
  user_id: number;
  server_id: number;
  server_rate: number;
  u: number;
  d: number;
  record_at: number;
};

export type NoticePublic = {
  id: number;
  title: string;
  img_url?: string | null;
  tags?: string | null;
  created_at: number;
};

export type PaginatedData<T> = {
  items: T[];
  total: number;
  page: number;
  size: number;
};
