import { endpoints } from "@/services/endpoints";
import { get, post } from "@/services/http";
import type { OrderDetail, OrderPublic, PaymentResult, PlanPeriodKey } from "@/types/api";

type CreateOrderParams = {
  planId: number;
  period: PlanPeriodKey;
  couponCode?: string;
};

export function getOrders(status?: number): Promise<OrderPublic[]> {
  return get<OrderPublic[]>(endpoints.orders.list(status));
}

export function getOrderDetail(tradeNo: string): Promise<OrderDetail> {
  return get<OrderDetail>(endpoints.orders.detail(tradeNo));
}

export function createOrder({ planId, period, couponCode }: CreateOrderParams): Promise<string> {
  return post<string>(endpoints.orders.create, {
    plan_id: planId,
    period,
    coupon_code: couponCode || undefined,
  });
}

export function checkoutOrder(tradeNo: string, method: number): Promise<PaymentResult> {
  return post<PaymentResult>(endpoints.orders.checkout, {
    trade_no: tradeNo,
    method,
  });
}

export function checkOrderStatus(tradeNo: string): Promise<number> {
  return get<number>(endpoints.orders.check(tradeNo));
}

export function cancelOrder(tradeNo: string): Promise<boolean> {
  return post<boolean>(endpoints.orders.cancel, {
    trade_no: tradeNo,
  });
}
