import { endpoints } from "@/services/endpoints";
import { get } from "@/services/http";
import type { PlanPublic } from "@/types/api";

export function getPlans(): Promise<PlanPublic[]> {
  return get<PlanPublic[]>(endpoints.plans.list);
}

export function getPlanDetail(planId: number): Promise<PlanPublic> {
  return get<PlanPublic>(endpoints.plans.detail(planId));
}
