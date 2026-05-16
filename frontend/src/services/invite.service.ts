import { endpoints } from "@/services/endpoints";
import { get, post } from "@/services/http";
import type { CommissionLog, InviteCode, InviteOverview } from "@/types/api";

export function getInviteOverview(): Promise<InviteOverview> {
  return get<InviteOverview>(endpoints.invite.overview);
}

export function createInviteCode(): Promise<InviteCode> {
  return post<InviteCode>(endpoints.invite.createCode);
}

export function getCommissionLogs(offset = 0, limit = 50): Promise<CommissionLog[]> {
  return get<CommissionLog[]>(endpoints.invite.commissionLogs(offset, limit));
}

export function transferCommission(amount: number): Promise<boolean> {
  return post<boolean>(endpoints.invite.transferCommission, { amount });
}
