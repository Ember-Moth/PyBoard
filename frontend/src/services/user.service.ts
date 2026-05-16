import { endpoints } from "@/services/endpoints";
import { get, patch, post } from "@/services/http";
import type {
  ChangePasswordParams,
  SecurityResetResult,
  SubscribeInfo,
  SubscribeServer,
  TrafficLog,
  UserProfile,
  UserProfileUpdate,
} from "@/types/api";

export function getUserProfile(): Promise<UserProfile> {
  return get<UserProfile>(endpoints.user.info);
}

export function updateUserProfile(data: UserProfileUpdate): Promise<boolean> {
  return patch<boolean>(endpoints.user.profile, data);
}

export function changeUserPassword({ oldPassword, newPassword }: ChangePasswordParams): Promise<boolean> {
  return post<boolean>(endpoints.user.changePassword, {
    old_password: oldPassword,
    new_password: newPassword,
  });
}

export function createQuickLoginUrl(redirect = "dashboard"): Promise<string> {
  return post<string>(endpoints.user.quickLoginUrl, { redirect }).then(normalizeQuickLoginUrl);
}

export function unbindTelegram(): Promise<boolean> {
  return post<boolean>(endpoints.user.unbindTelegram);
}

export function getSubscribeInfo(): Promise<SubscribeInfo> {
  return get<SubscribeInfo>(endpoints.user.subscribe);
}

export function getUserServers(): Promise<SubscribeServer[]> {
  return get<SubscribeServer[]>(endpoints.user.servers, { cache: "no-store" });
}

export function getUserStats(): Promise<number[]> {
  return get<number[]>(endpoints.user.stats);
}

export function getTrafficLogs(limit = 8): Promise<TrafficLog[]> {
  return get<TrafficLog[]>(endpoints.user.trafficLogs(limit));
}

export function resetUserSecurity(): Promise<SecurityResetResult> {
  return post<SecurityResetResult>(endpoints.user.resetSecurity);
}

function normalizeQuickLoginUrl(value: string): string {
  if (value.startsWith("/#/login?")) {
    return `/auth/login?${value.slice("/#/login?".length)}`;
  }

  try {
    const url = new URL(value);
    if (url.hash.startsWith("#/login?")) {
      url.pathname = "/auth/login";
      url.search = url.hash.slice("#/login".length);
      url.hash = "";
      return url.toString();
    }
  } catch {
    return value;
  }

  return value;
}
