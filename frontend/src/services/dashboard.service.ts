import { getNotices } from "@/services/notice.service";
import { getSubscribeInfo, getTrafficLogs, getUserConfig, getUserProfile, getUserStats } from "@/services/user.service";
import type { NoticePublic, PaginatedData, SubscribeInfo, TrafficLog, UserConfig, UserProfile } from "@/types/api";

export type DashboardData = {
  profile: UserProfile;
  subscribe: SubscribeInfo;
  stats: number[];
  trafficLogs: TrafficLog[];
  config: UserConfig;
  notices: PaginatedData<NoticePublic>;
  now: number;
};

export async function getDashboardData(): Promise<DashboardData> {
  const [profile, subscribe, stats, trafficLogs, config, notices] = await Promise.all([
    getUserProfile(),
    getSubscribeInfo(),
    getUserStats(),
    getTrafficLogs(8),
    getUserConfig(),
    getNotices(1, 5),
  ]);

  return {
    profile,
    subscribe,
    stats,
    trafficLogs,
    config,
    notices,
    now: Math.floor(Date.now() / 1000),
  };
}
