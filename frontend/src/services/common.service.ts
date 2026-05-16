import { endpoints } from "@/services/endpoints";
import { get } from "@/services/http";
import type { CommonConfig } from "@/types/api";

export function getCommonConfig(): Promise<CommonConfig> {
  return get<CommonConfig>(endpoints.common.config, { auth: false });
}
