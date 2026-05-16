import { endpoints } from "@/services/endpoints";
import { get } from "@/services/http";
import type { PaymentMethod } from "@/types/api";

export function getPaymentMethods(): Promise<PaymentMethod[]> {
  return get<PaymentMethod[]>(endpoints.paymentMethods.list);
}
