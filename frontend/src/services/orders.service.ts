import { getOrders } from "@/services/order.service";
import { getPaymentMethods } from "@/services/payment.service";
import { getUserConfig } from "@/services/user.service";
import type { OrderPublic, PaymentMethod, UserConfig } from "@/types/api";

export type OrdersPageData = {
  orders: OrderPublic[];
  payments: PaymentMethod[];
  config: UserConfig;
};

export async function getOrdersPageData(status?: number): Promise<OrdersPageData> {
  const [orders, payments, config] = await Promise.all([getOrders(status), getPaymentMethods(), getUserConfig()]);

  return {
    orders,
    payments,
    config,
  };
}
