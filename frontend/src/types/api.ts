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

export type SubscribeServer = {
  id?: number;
  type?: string;
  protocol?: string;
  name?: string;
  host?: string;
  port?: string | number;
  server_port?: number | null;
  rate?: number;
  network?: string;
  tls?: number | boolean | string | null;
  first_port?: string;
  multi_port?: boolean;
  cache_key?: string;
};

export type PlanPeriodKey =
  | "month_price"
  | "quarter_price"
  | "half_year_price"
  | "year_price"
  | "two_year_price"
  | "three_year_price"
  | "onetime_price"
  | "reset_price";

export type PlanPublic = {
  id: number;
  group_id: number;
  transfer_enable: number;
  device_limit?: number | null;
  name: string;
  speed_limit?: number | null;
  sort?: number | null;
  content?: string | null;
  month_price?: number | null;
  quarter_price?: number | null;
  half_year_price?: number | null;
  year_price?: number | null;
  two_year_price?: number | null;
  three_year_price?: number | null;
  onetime_price?: number | null;
  reset_price?: number | null;
  reset_traffic_method?: number | null;
  capacity_limit?: number | null;
  created_at: number;
};

export type PaymentMethod = {
  id: number;
  name: string;
  payment: string;
  icon?: string | null;
  handling_fee_fixed?: number | null;
  handling_fee_percent?: number | null;
};

export type OrderPublic = {
  id: number;
  plan_id: number;
  period: string;
  trade_no: string;
  total_amount: number;
  status: number;
  paid_at?: number | null;
  created_at: number;
};

export type OrderRead = OrderPublic & {
  handling_amount?: number | null;
  balance_amount?: number | null;
  updated_at: number;
};

export type OrderDetail = {
  order: OrderRead;
  plan: Partial<PlanPublic> | null;
};

export type PaymentResult = {
  type: -1 | 0 | 1;
  data: string | boolean;
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
