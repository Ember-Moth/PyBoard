import { endpoints } from "@/services/endpoints";
import { get, post } from "@/services/http";
import type { TicketCreateParams, TicketDetail, TicketPublic, WithdrawTicketParams } from "@/types/api";

export function getTickets(offset = 0, limit = 50): Promise<TicketPublic[]> {
  return get<TicketPublic[]>(endpoints.tickets.list(offset, limit));
}

export function getTicketDetail(ticketId: number): Promise<TicketDetail> {
  return get<TicketDetail>(endpoints.tickets.detail(ticketId));
}

export function createTicket(data: TicketCreateParams): Promise<TicketDetail> {
  return post<TicketDetail>(endpoints.tickets.create, data);
}

export function replyTicket(ticketId: number, message: string): Promise<TicketDetail> {
  return post<TicketDetail>(endpoints.tickets.reply(ticketId), { message });
}

export function closeTicket(ticketId: number): Promise<boolean> {
  return post<boolean>(endpoints.tickets.close(ticketId));
}

export function createWithdrawTicket({ withdrawMethod, withdrawAccount }: WithdrawTicketParams): Promise<TicketDetail> {
  return post<TicketDetail>(endpoints.tickets.withdraw, {
    withdraw_method: withdrawMethod,
    withdraw_account: withdrawAccount,
  });
}
