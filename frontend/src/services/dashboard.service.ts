import { getCommonConfig } from "@/services/common.service";
import { getNotices } from "@/services/notice.service";
import { getSubscribeInfo, getTrafficLogs, getUserProfile, getUserStats } from "@/services/user.service";
import type { CommonConfig, NoticePublic, PaginatedData, SubscribeInfo, TrafficLog, UserProfile } from "@/types/api";

export type DashboardData = {
  profile: UserProfile;
  subscribe: SubscribeInfo;
  stats: number[];
  trafficLogs: TrafficLog[];
  config: CommonConfig;
  notices: PaginatedData<NoticePublic>;
  now: number;
};

export async function getDashboardData(): Promise<DashboardData> {
  const [profile, subscribe, stats, trafficLogs, config, notices] = await Promise.all([
    getUserProfile(),
    getSubscribeInfo(),
    getUserStats(),
    getTrafficLogs(8),
    getCommonConfig(),
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
