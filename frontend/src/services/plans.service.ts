import { getPaymentMethods } from "@/services/payment.service";
import { getPlans } from "@/services/plan.service";
import { getSubscribeInfo, getUserConfig } from "@/services/user.service";
import type { PaymentMethod, PlanPublic, SubscribeInfo, UserConfig } from "@/types/api";

export type PlansPageData = {
  plans: PlanPublic[];
  payments: PaymentMethod[];
  subscribe: SubscribeInfo;
  config: UserConfig;
};

export async function getPlansPageData(): Promise<PlansPageData> {
  const [plans, payments, subscribe, config] = await Promise.all([
    getPlans(),
    getPaymentMethods(),
    getSubscribeInfo(),
    getUserConfig(),
  ]);

  return {
    plans,
    payments,
    subscribe,
    config,
  };
}
