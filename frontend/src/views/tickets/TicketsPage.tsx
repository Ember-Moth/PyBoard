"use client";

import {
  Alert,
  Box,
  Button,
  ButtonBase,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { IconCircleCheck, IconHeadset, IconMessageCircle, IconPlus, IconRefresh, IconSend } from "@tabler/icons-react";
import type { Dispatch, FormEvent, ReactNode, SetStateAction } from "react";
import { useEffect, useMemo, useState } from "react";
import CustomTextField from "@/components/forms/CustomTextField";
import PageContainer from "@/components/layout/PageContainer";
import { formatDateTime } from "@/lib/format";
import { getCommonConfig } from "@/services/common.service";
import { closeTicket, createTicket, getTicketDetail, getTickets, replyTicket } from "@/services/ticket.service";
import type { TicketCreateParams, TicketDetail, TicketLevel, TicketPublic } from "@/types/api";

const TICKET_LEVELS: Array<{ value: TicketLevel; label: string; description: string }> = [
  { value: 0, label: "普通", description: "一般咨询" },
  { value: 1, label: "重要", description: "影响使用" },
  { value: 2, label: "紧急", description: "服务不可用" },
];

const EMPTY_FORM: TicketCreateParams = {
  subject: "",
  level: 0,
  message: "",
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<TicketPublic[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [form, setForm] = useState<TicketCreateParams>(EMPTY_FORM);
  const [replyMessage, setReplyMessage] = useState("");
  const [ticketStatusSetting, setTicketStatusSetting] = useState(0);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [creating, setCreating] = useState(false);
  const [replying, setReplying] = useState(false);
  const [closing, setClosing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const openTicket = useMemo(() => tickets.find((ticket) => ticket.status === 0), [tickets]);
  const selectedTicket = detail?.ticket || tickets.find((ticket) => ticket.id === selectedId) || null;
  const lastMessage = detail?.messages.at(-1);
  const canReply = Boolean(detail && detail.ticket.status === 0 && !lastMessage?.is_me);
  const createDisabled = ticketStatusSetting === 2 || creating;

  const loadTickets = async (selectFirst: boolean) => {
    setError("");
    setLoadingList(true);
    try {
      const [nextTickets, config] = await Promise.all([getTickets(), getCommonConfig()]);
      setTickets(nextTickets);
      setTicketStatusSetting(config.ticket_status || 0);
      if (selectFirst) {
        const firstId = nextTickets[0]?.id ?? null;
        setSelectedId(firstId);
        if (!firstId) {
          setDetail(null);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "工单列表加载失败");
    } finally {
      setLoadingList(false);
    }
  };

  const loadDetail = async (ticketId: number) => {
    setError("");
    setLoadingDetail(true);
    try {
      setDetail(await getTicketDetail(ticketId));
      setReplyMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "工单详情加载失败");
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    void loadTickets(true);
  }, []);

  useEffect(() => {
    if (selectedId) {
      void loadDetail(selectedId);
    }
  }, [selectedId]);

  const submitTicket = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setCreating(true);
    try {
      const created = await createTicket(form);
      setForm(EMPTY_FORM);
      setDetail(created);
      setSelectedId(created.ticket.id);
      setSuccess("工单已创建");
      await loadTickets(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建工单失败");
    } finally {
      setCreating(false);
    }
  };

  const submitReply = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!detail) {
      return;
    }
    setError("");
    setSuccess("");
    setReplying(true);
    try {
      const nextDetail = await replyTicket(detail.ticket.id, replyMessage);
      setDetail(nextDetail);
      setReplyMessage("");
      setSuccess("回复已提交");
      await loadTickets(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "回复工单失败");
    } finally {
      setReplying(false);
    }
  };

  const closeSelectedTicket = async () => {
    if (!detail) {
      return;
    }
    setError("");
    setSuccess("");
    setClosing(true);
    try {
      await closeTicket(detail.ticket.id);
      await Promise.all([loadDetail(detail.ticket.id), loadTickets(false)]);
      setSuccess("工单已关闭");
    } catch (err) {
      setError(err instanceof Error ? err.message : "关闭工单失败");
    } finally {
      setClosing(false);
    }
  };

  return (
    <PageContainer title="工单支持" description="创建工单、查看回复并关闭已解决的问题">
      <Stack spacing={3}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography variant="h3">工单支持</Typography>
            <Typography variant="body1" color="text.secondary" mt={0.5}>
              提交问题、查看客服回复，并在问题解决后关闭工单。
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<IconRefresh size={18} />} onClick={() => void loadTickets(false)}>
            刷新列表
          </Button>
        </Stack>

        {ticketStatusSetting === 1 ? <Alert severity="info">当前站点要求已购买套餐的用户才能发起工单。</Alert> : null}
        {ticketStatusSetting === 2 ? <Alert severity="warning">当前站点暂未开放新工单。</Alert> : null}
        {openTicket ? <Alert severity="info">同一时间只能保留一个未关闭工单。</Alert> : null}
        {error ? <Alert severity="error">{error}</Alert> : null}
        {success ? <Alert severity="success">{success}</Alert> : null}

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, lg: 4 }}>
            <Stack spacing={3}>
              <Card elevation={9}>
                <CardContent>
                  <Stack spacing={2}>
                    <SectionHeader
                      icon={<IconPlus size={20} />}
                      title="新建工单"
                      description="请描述具体问题，客服会在工单内回复。"
                    />
                    <Box component="form" onSubmit={submitTicket}>
                      <Stack spacing={2}>
                        <CustomTextField
                          label="主题"
                          value={form.subject}
                          onChange={(event) => setForm((current) => ({ ...current, subject: event.target.value }))}
                          required
                          fullWidth
                          disabled={createDisabled}
                        />
                        <FormControl fullWidth disabled={createDisabled}>
                          <InputLabel id="ticket-level-label">优先级</InputLabel>
                          <Select
                            labelId="ticket-level-label"
                            label="优先级"
                            value={String(form.level)}
                            onChange={handleLevelChange(setForm)}
                          >
                            {TICKET_LEVELS.map((level) => (
                              <MenuItem value={String(level.value)} key={level.value}>
                                {level.label} - {level.description}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                        <CustomTextField
                          label="问题描述"
                          value={form.message}
                          onChange={(event) => setForm((current) => ({ ...current, message: event.target.value }))}
                          required
                          fullWidth
                          multiline
                          minRows={5}
                          disabled={createDisabled}
                        />
                        <Button
                          type="submit"
                          variant="contained"
                          startIcon={<IconSend size={18} />}
                          disabled={createDisabled}
                        >
                          {creating ? "提交中..." : "提交工单"}
                        </Button>
                      </Stack>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>

              <Card elevation={9}>
                <CardContent>
                  <Stack spacing={2}>
                    <SectionHeader
                      icon={<IconHeadset size={20} />}
                      title="我的工单"
                      description="选择一条工单查看会话内容。"
                    />
                    {loadingList ? (
                      <TicketListSkeleton />
                    ) : tickets.length ? (
                      <Stack spacing={1.5}>
                        {tickets.map((ticket) => (
                          <TicketListItem
                            ticket={ticket}
                            selected={ticket.id === selectedId}
                            onSelect={() => setSelectedId(ticket.id)}
                            key={ticket.id}
                          />
                        ))}
                      </Stack>
                    ) : (
                      <Box py={3} textAlign="center">
                        <Typography color="text.secondary">暂无工单</Typography>
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, lg: 8 }}>
            <Card elevation={9}>
              <CardContent>
                {loadingDetail ? (
                  <TicketDetailSkeleton />
                ) : selectedTicket && detail ? (
                  <Stack spacing={3}>
                    <Stack
                      direction={{ xs: "column", md: "row" }}
                      spacing={2}
                      justifyContent="space-between"
                      alignItems={{ xs: "flex-start", md: "center" }}
                    >
                      <Box>
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                          <Typography variant="h4">{detail.ticket.subject}</Typography>
                          <Chip
                            size="small"
                            label={ticketLevelLabel(detail.ticket.level)}
                            color={ticketLevelColor(detail.ticket.level)}
                          />
                          <Chip
                            size="small"
                            label={ticketStatusLabel(detail.ticket)}
                            color={ticketStatusColor(detail.ticket)}
                          />
                        </Stack>
                        <Typography variant="body2" color="text.secondary" mt={0.75}>
                          #{detail.ticket.id} 创建于 {formatDateTime(detail.ticket.created_at)}
                        </Typography>
                      </Box>
                      <Button
                        variant="outlined"
                        color="warning"
                        startIcon={<IconCircleCheck size={18} />}
                        onClick={() => void closeSelectedTicket()}
                        disabled={detail.ticket.status !== 0 || closing}
                      >
                        {closing ? "关闭中..." : "关闭工单"}
                      </Button>
                    </Stack>

                    <Divider />

                    <Stack spacing={2}>
                      {detail.messages.map((message) => (
                        <MessageBubble message={message} key={message.id} />
                      ))}
                    </Stack>

                    <Divider />

                    <Box component="form" onSubmit={submitReply}>
                      <Stack spacing={2}>
                        {!canReply ? (
                          <Alert severity={detail.ticket.status === 0 ? "info" : "warning"}>
                            {detail.ticket.status === 0 ? "请等待客服回复后再继续补充。" : "工单已关闭，不能继续回复。"}
                          </Alert>
                        ) : null}
                        <CustomTextField
                          label="回复内容"
                          value={replyMessage}
                          onChange={(event) => setReplyMessage(event.target.value)}
                          multiline
                          minRows={4}
                          fullWidth
                          required
                          disabled={!canReply || replying}
                        />
                        <Box>
                          <Button
                            type="submit"
                            variant="contained"
                            startIcon={<IconMessageCircle size={18} />}
                            disabled={!canReply || replying || !replyMessage.trim()}
                          >
                            {replying ? "提交中..." : "回复工单"}
                          </Button>
                        </Box>
                      </Stack>
                    </Box>
                  </Stack>
                ) : (
                  <EmptyDetail />
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Stack>
    </PageContainer>
  );
}

function SectionHeader({ icon, title, description }: { icon: ReactNode; title: string; description: string }) {
  return (
    <Stack direction="row" spacing={1.5} alignItems="flex-start">
      <Box color="primary.main" mt={0.2}>
        {icon}
      </Box>
      <Box>
        <Typography variant="h5">{title}</Typography>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Box>
    </Stack>
  );
}

function TicketListItem({
  ticket,
  selected,
  onSelect,
}: {
  ticket: TicketPublic;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <ButtonBase
      onClick={onSelect}
      sx={{
        border: "1px solid",
        borderColor: selected ? "primary.main" : "divider",
        borderRadius: 2,
        display: "block",
        p: 1.5,
        textAlign: "left",
        width: "100%",
      }}
    >
      <Stack spacing={1}>
        <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="flex-start">
          <Typography fontWeight={700} noWrap>
            {ticket.subject}
          </Typography>
          <Chip size="small" label={ticketStatusLabel(ticket)} color={ticketStatusColor(ticket)} />
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
          <Chip
            size="small"
            variant="outlined"
            label={ticketLevelLabel(ticket.level)}
            color={ticketLevelColor(ticket.level)}
          />
          <Typography variant="caption" color="text.secondary">
            {formatDateTime(ticket.created_at)}
          </Typography>
        </Stack>
      </Stack>
    </ButtonBase>
  );
}

function MessageBubble({ message }: { message: TicketDetail["messages"][number] }) {
  return (
    <Stack alignItems={message.is_me ? "flex-end" : "flex-start"}>
      <Box
        sx={{
          bgcolor: message.is_me ? "primary.main" : "grey.100",
          borderRadius: 2,
          color: message.is_me ? "primary.contrastText" : "text.primary",
          maxWidth: "min(100%, 680px)",
          px: 2,
          py: 1.5,
        }}
      >
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {message.message}
        </Typography>
        <Typography
          variant="caption"
          sx={{ color: message.is_me ? "primary.contrastText" : "text.secondary", display: "block", mt: 1 }}
        >
          {message.is_me ? "我" : "客服"} · {formatDateTime(message.created_at)}
        </Typography>
      </Box>
    </Stack>
  );
}

function EmptyDetail() {
  return (
    <Box py={8} textAlign="center">
      <IconHeadset size={44} color="#90a4ae" />
      <Typography variant="h5" mt={2}>
        选择工单
      </Typography>
      <Typography color="text.secondary" mt={0.5}>
        从左侧列表选择工单，或提交一个新的问题。
      </Typography>
    </Box>
  );
}

function TicketListSkeleton() {
  return (
    <Stack spacing={1.5}>
      {[0, 1, 2].map((item) => (
        <Box key={item} sx={{ border: "1px solid", borderColor: "divider", borderRadius: 2, p: 1.5 }}>
          <Skeleton width="70%" height={24} />
          <Skeleton width="45%" height={20} />
        </Box>
      ))}
    </Stack>
  );
}

function TicketDetailSkeleton() {
  return (
    <Stack spacing={2}>
      <Skeleton width="45%" height={38} />
      <Skeleton width="30%" height={20} />
      <Divider />
      <Skeleton height={90} />
      <Skeleton height={90} width="80%" sx={{ alignSelf: "flex-end" }} />
      <Divider />
      <Skeleton height={120} />
    </Stack>
  );
}

function handleLevelChange(setForm: Dispatch<SetStateAction<TicketCreateParams>>) {
  return (event: SelectChangeEvent) => {
    setForm((current) => ({ ...current, level: Number(event.target.value) as TicketLevel }));
  };
}

function ticketLevelLabel(level: number): string {
  return TICKET_LEVELS.find((item) => item.value === level)?.label || "普通";
}

function ticketLevelColor(level: number): "default" | "info" | "warning" {
  if (level === 2) {
    return "warning";
  }
  if (level === 1) {
    return "info";
  }
  return "default";
}

function ticketStatusLabel(ticket: Pick<TicketPublic, "status" | "reply_status">): string {
  if (ticket.status !== 0) {
    return "已关闭";
  }
  return ticket.reply_status === 1 ? "客服已回复" : "等待回复";
}

function ticketStatusColor(ticket: Pick<TicketPublic, "status" | "reply_status">): "default" | "info" | "warning" {
  if (ticket.status !== 0) {
    return "default";
  }
  return ticket.reply_status === 1 ? "info" : "warning";
}
