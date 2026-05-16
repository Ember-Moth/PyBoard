import { getCommonConfig } from "@/services/common.service";
import { getOrders } from "@/services/order.service";
import { getPaymentMethods } from "@/services/payment.service";
import type { CommonConfig, OrderPublic, PaymentMethod } from "@/types/api";

export type OrdersPageData = {
  orders: OrderPublic[];
  payments: PaymentMethod[];
  config: CommonConfig;
};

export async function getOrdersPageData(status?: number): Promise<OrdersPageData> {
  const [orders, payments, config] = await Promise.all([getOrders(status), getPaymentMethods(), getCommonConfig()]);

  return {
    orders,
    payments,
    config,
  };
}
