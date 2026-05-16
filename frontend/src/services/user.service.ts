import { endpoints } from "@/services/endpoints";
import { get, post } from "@/services/http";
import type { SubscribeInfo, TrafficLog, UserConfig, UserProfile } from "@/types/api";

export function getUserProfile(): Promise<UserProfile> {
  return get<UserProfile>(endpoints.user.info);
}

export function getSubscribeInfo(): Promise<SubscribeInfo> {
  return get<SubscribeInfo>(endpoints.user.subscribe);
}

export function getUserStats(): Promise<number[]> {
  return get<number[]>(endpoints.user.stats);
}

export function getTrafficLogs(limit = 8): Promise<TrafficLog[]> {
  return get<TrafficLog[]>(endpoints.user.trafficLogs(limit));
}

export function getUserConfig(): Promise<UserConfig> {
  return get<UserConfig>(endpoints.comm.config);
}

export function resetUserSecurity(): Promise<unknown> {
  return post<unknown>(endpoints.user.resetSecurity);
}
