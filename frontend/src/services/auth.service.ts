import { endpoints } from "@/services/endpoints";
import { get, post } from "@/services/http";
import type { TokenResponse, UserProfile } from "@/types/api";

type LoginParams = {
  email: string;
  password: string;
  recaptchaData?: string;
};

type RegisterParams = LoginParams & {
  inviteCode?: string;
  emailCode?: string;
};

type SendEmailVerifyParams = {
  email: string;
  isForget?: boolean;
  recaptchaData?: string;
};

type ForgetPasswordParams = LoginParams & {
  emailCode: string;
};

export function login({ email, password, recaptchaData }: LoginParams): Promise<TokenResponse> {
  return post<TokenResponse>(
    endpoints.auth.login,
    {
      email,
      password,
      recaptcha_data: recaptchaData || undefined,
    },
    { auth: false },
  );
}

export function register({
  email,
  password,
  inviteCode,
  emailCode,
  recaptchaData,
}: RegisterParams): Promise<TokenResponse> {
  return post<TokenResponse>(
    endpoints.auth.register,
    {
      email,
      password,
      invite_code: inviteCode || undefined,
      email_code: emailCode || undefined,
      recaptcha_data: recaptchaData || undefined,
    },
    { auth: false },
  );
}

export function quickLogin(verify: string): Promise<TokenResponse> {
  return get<TokenResponse>(endpoints.auth.tokenLogin(verify), { auth: false });
}

export function sendEmailVerify({ email, isForget, recaptchaData }: SendEmailVerifyParams): Promise<boolean> {
  return post<boolean>(
    endpoints.auth.emailVerify,
    {
      email,
      isforget: isForget ? 1 : undefined,
      recaptcha_data: recaptchaData || undefined,
    },
    { auth: false },
  );
}

export function forgetPassword({ email, emailCode, password, recaptchaData }: ForgetPasswordParams): Promise<boolean> {
  return post<boolean>(
    endpoints.auth.forget,
    {
      email,
      email_code: emailCode,
      password,
      recaptcha_data: recaptchaData || undefined,
    },
    { auth: false },
  );
}

export function getCurrentUser(): Promise<UserProfile> {
  return get<UserProfile>(endpoints.auth.me);
}
