import { endpoints } from "@/services/endpoints";
import { get } from "@/services/http";
import type { NoticePublic, PaginatedData } from "@/types/api";

export function getNotices(page = 1, size = 5): Promise<PaginatedData<NoticePublic>> {
  return get<PaginatedData<NoticePublic>>(endpoints.notices.list(page, size), { auth: false });
}
