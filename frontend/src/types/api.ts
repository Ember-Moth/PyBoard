export type ApiResponse<T> = {
  code: number;
  msg: string;
  data: T | null;
};

export type TokenResponse = {
  auth_token: string;
};

export type CommonConfig = {
  logo?: string;
  stop_register?: number;
  app_name?: string;
  app_description?: string;
  app_url?: string;
  subscribe_url?: string;
  subscribe_path?: string;
  try_out_plan_id?: number;
  try_out_hour?: number;
  tos_url?: string;
  currency?: string;
  currency_symbol?: string;
  is_email_verify?: number;
  is_invite_force?: number;
  is_email_whitelist?: number;
  email_whitelist_suffix?: string[] | 0;
  is_recaptcha?: number;
  recaptcha_provider?: string;
  recaptcha_site_key?: string;
  turnstile_site_key?: string;
  is_telegram?: number;
  telegram_discuss_link?: string;
  ticket_status?: number;
  stripe_pk?: string;
  invite_gen_limit?: number;
  withdraw_methods?: string[];
  withdraw_close?: number;
  commission_withdraw_limit?: number;
  commission_distribution_enable?: number;
  commission_distribution_l1?: number | null;
  commission_distribution_l2?: number | null;
  commission_distribution_l3?: number | null;
};

export type UserProfile = {
  email: string;
  transfer_enable: number;
  device_limit?: number | null;
  last_login_at?: number | null;
  created_at: number;
  banned: boolean;
  auto_renewal?: number;
  remind_expire?: number;
  remind_traffic?: number;
  expired_at?: number | null;
  balance: number;
  commission_balance: number;
  plan_id?: number | null;
  discount?: number | null;
  commission_rate?: number | null;
  telegram_id?: number | null;
  uuid: string;
  avatar_url?: string;
};

export type UserProfileUpdate = {
  auto_renewal?: number;
  remind_expire?: number;
  remind_traffic?: number;
};

export type ChangePasswordParams = {
  oldPassword: string;
  newPassword: string;
};

export type SecurityResetResult = {
  uuid: string;
  token: string;
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

export type TicketLevel = 0 | 1 | 2;

export type TicketPublic = {
  id: number;
  user_id: number;
  subject: string;
  level: TicketLevel;
  status: number;
  reply_status: number;
  created_at: number;
};

export type TicketRead = TicketPublic & {
  updated_at: number;
};

export type TicketMessage = {
  id: number;
  user_id: number;
  ticket_id: number;
  message: string;
  is_me?: boolean | null;
  created_at: number;
};

export type TicketDetail = {
  ticket: TicketRead;
  messages: TicketMessage[];
};

export type TicketCreateParams = {
  subject: string;
  level: TicketLevel;
  message: string;
};

export type WithdrawTicketParams = {
  withdrawMethod: string;
  withdrawAccount: string;
};

export type InviteCode = {
  id: number;
  user_id: number;
  code: string;
  status: number;
  pv: number;
  created_at: number;
  updated_at?: number;
};

export type InviteOverview = {
  codes: InviteCode[];
  stat: [
    registeredCount: number,
    paidCommission: number,
    pendingCommission: number,
    commissionRate: number,
    commissionBalance: number,
  ];
};

export type CommissionLog = {
  id: number;
  invite_user_id: number;
  user_id: number;
  trade_no: string;
  order_amount: number;
  get_amount: number;
  created_at: number;
};
