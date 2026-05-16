import { getCommonConfig } from "@/services/common.service";
import { getPaymentMethods } from "@/services/payment.service";
import { getPlans } from "@/services/plan.service";
import { getSubscribeInfo } from "@/services/user.service";
import type { CommonConfig, PaymentMethod, PlanPublic, SubscribeInfo } from "@/types/api";

export type PlansPageData = {
  plans: PlanPublic[];
  payments: PaymentMethod[];
  subscribe: SubscribeInfo;
  config: CommonConfig;
};

export async function getPlansPageData(): Promise<PlansPageData> {
  const [plans, payments, subscribe, config] = await Promise.all([
    getPlans(),
    getPaymentMethods(),
    getSubscribeInfo(),
    getCommonConfig(),
  ]);

  return {
    plans,
    payments,
    subscribe,
    config,
  };
}
