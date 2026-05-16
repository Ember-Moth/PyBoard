import { getSubscribeInfo, getUserServers, resetUserSecurity } from "@/services/user.service";
import type { SubscribeInfo, SubscribeServer } from "@/types/api";

export type SubscribePageData = {
  subscribe: SubscribeInfo;
  servers: SubscribeServer[];
  now: number;
};

export async function getSubscribePageData(): Promise<SubscribePageData> {
  const [subscribe, servers] = await Promise.all([getSubscribeInfo(), getUserServers()]);

  return {
    subscribe,
    servers,
    now: Math.floor(Date.now() / 1000),
  };
}

export { resetUserSecurity };
