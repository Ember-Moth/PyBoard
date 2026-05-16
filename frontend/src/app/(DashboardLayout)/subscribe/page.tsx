"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  IconCopy,
  IconExternalLink,
  IconLink,
  IconRefresh,
  IconServer,
  IconShieldLock,
  IconWifi,
} from "@tabler/icons-react";

import PageContainer from "@/app/(DashboardLayout)/components/container/PageContainer";
import { formatBytes, formatDateTime, percent } from "@/lib/format";
import { getSubscribePageData, resetUserSecurity, type SubscribePageData } from "@/services/subscribe.service";
import type { SubscribeInfo, SubscribeServer } from "@/types/api";

const CLIENT_LINKS = [
  { key: "general", name: "通用订阅", flag: "general" },
  { key: "clash", name: "Clash / Mihomo", flag: "clash-meta" },
  { key: "singbox", name: "sing-box", flag: "sing-box/1.12.0" },
  { key: "surge", name: "Surge", flag: "surge" },
  { key: "shadowrocket", name: "Shadowrocket", flag: "shadowrocket" },
] as const;

export default function SubscribePage() {
  const [data, setData] = useState<SubscribePageData | null>(null);
  const [error, setError] = useState("");
  const [copiedKey, setCopiedKey] = useState("");
  const [resetting, setResetting] = useState(false);

  const loadSubscribe = async () => {
    setError("");
    try {
      setData(await getSubscribePageData());
    } catch (err) {
      setError(err instanceof Error ? err.message : "订阅信息加载失败");
    }
  };

  useEffect(() => {
    let cancelled = false;
    getSubscribePageData()
      .then((nextData) => {
        if (!cancelled) {
          setData(nextData);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "订阅信息加载失败");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const usage = useMemo(() => {
    if (!data) {
      return { used: 0, total: 0, remaining: 0, value: 0 };
    }
    const used = (data.subscribe.u || 0) + (data.subscribe.d || 0);
    const total = data.subscribe.transfer_enable || 0;
    return {
      used,
      total,
      remaining: Math.max(total - used, 0),
      value: percent(used, total),
    };
  }, [data]);

  const status = useMemo(() => {
    if (!data) {
      return { label: "加载中", color: "default" as const, message: "" };
    }
    return getSubscribeStatus(data.subscribe, data.now, usage.used);
  }, [data, usage.used]);

  const copyText = async (key: string, value: string) => {
    if (!value) {
      return;
    }
    await navigator.clipboard.writeText(value);
    setCopiedKey(key);
    window.setTimeout(() => setCopiedKey(""), 1800);
  };

  const openUrl = (url: string) => {
    if (!url) {
      return;
    }
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const resetSecurity = async () => {
    setResetting(true);
    setError("");
    try {
      await resetUserSecurity();
      await loadSubscribe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置订阅失败");
    } finally {
      setResetting(false);
    }
  };

  if (!data && !error) {
    return <SubscribeSkeleton />;
  }

  return (
    <PageContainer title="我的订阅" description="管理订阅链接、可用节点和客户端导入方式">
      <Stack spacing={3}>
        <Box>
          <Typography variant="h3">我的订阅</Typography>
          <Typography variant="body1" color="text.secondary" mt={0.5}>
            查看套餐状态、复制订阅链接和检查可用节点。
          </Typography>
        </Box>

        {error ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={() => void loadSubscribe()}>
                重试
              </Button>
            }
          >
            {error}
          </Alert>
        ) : null}

        {data ? (
          <>
            <Card elevation={9}>
              <CardContent>
                <Stack spacing={3}>
                  <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                    <Box>
                      <Stack direction="row" spacing={1.5} alignItems="center" mb={1}>
                        <Typography variant="h4">{data.subscribe.plan?.name || "暂无套餐"}</Typography>
                        <Chip size="small" label={status.label} color={status.color} />
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        {status.message}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      <Button
                        variant="contained"
                        startIcon={<IconCopy size={18} />}
                        disabled={!data.subscribe.subscribe_url}
                        onClick={() => void copyText("main", data.subscribe.subscribe_url)}
                      >
                        {copiedKey === "main" ? "已复制" : "复制订阅"}
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<IconExternalLink size={18} />}
                        disabled={!data.subscribe.subscribe_url}
                        onClick={() => openUrl(data.subscribe.subscribe_url)}
                      >
                        打开订阅
                      </Button>
                      <Button
                        variant="outlined"
                        color="secondary"
                        startIcon={<IconRefresh size={18} />}
                        disabled={resetting}
                        onClick={() => void resetSecurity()}
                      >
                        {resetting ? "重置中" : "重置订阅"}
                      </Button>
                    </Stack>
                  </Stack>

                  <Box>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle2">流量使用</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {usage.value}%
                      </Typography>
                    </Stack>
                    <LinearProgress variant="determinate" value={usage.value} sx={{ height: 10, borderRadius: 5 }} />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6, lg: 3 }}>
                <MetricCard
                  title="已用流量"
                  value={formatBytes(usage.used)}
                  subtitle={`剩余 ${formatBytes(usage.remaining)}`}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6, lg: 3 }}>
                <MetricCard
                  title="套餐总量"
                  value={formatBytes(usage.total)}
                  subtitle={`上传 ${formatBytes(data.subscribe.u)}`}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6, lg: 3 }}>
                <MetricCard
                  title="到期时间"
                  value={formatDateTime(data.subscribe.expired_at)}
                  subtitle={formatResetDay(data.subscribe.reset_day)}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6, lg: 3 }}>
                <MetricCard
                  title="在线设备"
                  value={`${data.subscribe.alive_ip || 0}`}
                  subtitle={`限制 ${data.subscribe.device_limit || "不限"}`}
                />
              </Grid>
            </Grid>

            <Card elevation={9}>
              <CardContent>
                <Stack spacing={2}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <IconLink size={20} />
                    <Typography variant="h5">订阅链接</Typography>
                  </Stack>
                  <Box
                    sx={{
                      border: "1px solid",
                      borderColor: "divider",
                      borderRadius: 1,
                      bgcolor: "grey.100",
                      px: 2,
                      py: 1.5,
                    }}
                  >
                    <Typography variant="body2" sx={{ wordBreak: "break-all", fontFamily: "monospace" }}>
                      {data.subscribe.subscribe_url || "暂无订阅链接"}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            <Card elevation={9}>
              <CardContent>
                <Stack spacing={2}>
                  <Typography variant="h5">客户端链接</Typography>
                  <Grid container spacing={2}>
                    {CLIENT_LINKS.map((client) => {
                      const url = withFlag(data.subscribe.subscribe_url, client.flag);
                      return (
                        <Grid key={client.key} size={{ xs: 12, sm: 6, lg: 4 }}>
                          <Stack
                            direction="row"
                            spacing={1}
                            alignItems="center"
                            justifyContent="space-between"
                            sx={{
                              border: "1px solid",
                              borderColor: "divider",
                              borderRadius: 1,
                              px: 1.5,
                              py: 1.25,
                              minHeight: 64,
                            }}
                          >
                            <Box minWidth={0}>
                              <Typography variant="subtitle2" noWrap>
                                {client.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {client.flag}
                              </Typography>
                            </Box>
                            <Stack direction="row" spacing={0.5}>
                              <Button
                                variant="text"
                                size="small"
                                disabled={!url}
                                onClick={() => void copyText(client.key, url)}
                              >
                                {copiedKey === client.key ? "已复制" : "复制"}
                              </Button>
                              <Button variant="text" size="small" disabled={!url} onClick={() => openUrl(url)}>
                                打开
                              </Button>
                            </Stack>
                          </Stack>
                        </Grid>
                      );
                    })}
                  </Grid>
                </Stack>
              </CardContent>
            </Card>

            <Card elevation={9}>
              <CardContent>
                <Stack spacing={2}>
                  <Stack direction="row" alignItems="center" justifyContent="space-between">
                    <Stack direction="row" spacing={1} alignItems="center">
                      <IconServer size={20} />
                      <Typography variant="h5">可用节点</Typography>
                    </Stack>
                    <Chip size="small" label={`${data.servers.length} 个节点`} />
                  </Stack>

                  <TableContainer>
                    <Table sx={{ minWidth: 760 }}>
                      <TableHead>
                        <TableRow>
                          <TableCell>节点</TableCell>
                          <TableCell>协议</TableCell>
                          <TableCell>入口</TableCell>
                          <TableCell>网络</TableCell>
                          <TableCell>倍率</TableCell>
                          <TableCell>安全</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {data.servers.length ? (
                          data.servers.map((server, index) => (
                            <TableRow key={server.cache_key || `${server.name || "server"}-${index}`}>
                              <TableCell>
                                <Typography variant="subtitle2">{server.name || "未命名节点"}</Typography>
                              </TableCell>
                              <TableCell>{formatProtocol(server.protocol)}</TableCell>
                              <TableCell>{formatServerEntry(server)}</TableCell>
                              <TableCell>
                                <Stack direction="row" spacing={0.75} alignItems="center">
                                  <IconWifi size={16} />
                                  <span>{server.network || "tcp"}</span>
                                </Stack>
                              </TableCell>
                              <TableCell>{server.rate || 1}x</TableCell>
                              <TableCell>
                                <Stack direction="row" spacing={0.75} alignItems="center">
                                  <IconShieldLock size={16} />
                                  <span>{isTlsEnabled(server.tls) ? "TLS" : "常规"}</span>
                                </Stack>
                              </TableCell>
                            </TableRow>
                          ))
                        ) : (
                          <TableRow>
                            <TableCell colSpan={6} align="center">
                              暂无可用节点
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Stack>
              </CardContent>
            </Card>
          </>
        ) : null}
      </Stack>
    </PageContainer>
  );
}

function SubscribeSkeleton() {
  return (
    <Stack spacing={3}>
      <Skeleton variant="rounded" height={170} />
      <Grid container spacing={3}>
        {[1, 2, 3, 4].map((item) => (
          <Grid key={item} size={{ xs: 12, md: 6, lg: 3 }}>
            <Skeleton variant="rounded" height={120} />
          </Grid>
        ))}
      </Grid>
      <Skeleton variant="rounded" height={280} />
    </Stack>
  );
}

function MetricCard({ title, value, subtitle }: { title: string; value: string; subtitle: string }) {
  return (
    <Card elevation={9}>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" mt={1}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary" mt={1}>
          {subtitle}
        </Typography>
      </CardContent>
    </Card>
  );
}

function getSubscribeStatus(subscribe: SubscribeInfo, now: number, used: number) {
  const expiredAt = subscribe.expired_at || 0;
  if (!subscribe.plan) {
    return { label: "未购套餐", color: "warning" as const, message: "购买套餐后即可生成订阅并使用节点。" };
  }
  if (expiredAt > 0 && expiredAt <= now) {
    return { label: "已过期", color: "warning" as const, message: "套餐已过期，请续费或购买新套餐。" };
  }
  if (subscribe.transfer_enable > 0 && used >= subscribe.transfer_enable) {
    return { label: "流量用尽", color: "warning" as const, message: "可续费、变更套餐或等待下次流量重置。" };
  }
  return { label: "正常", color: "success" as const, message: "订阅状态正常，节点列表可用。" };
}

function withFlag(url: string, flag: string): string {
  if (!url) {
    return "";
  }
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}flag=${encodeURIComponent(flag)}`;
}

function formatProtocol(value?: string): string {
  if (!value) {
    return "-";
  }
  return value.toUpperCase();
}

function formatServerEntry(server: SubscribeServer): string {
  const host = server.host || "-";
  const port = server.first_port || server.server_port || server.port || "";
  return port ? `${host}:${port}` : host;
}

function formatResetDay(value?: number | null): string {
  return value ? `重置剩余 ${value} 天` : "重置未配置";
}

function isTlsEnabled(value: SubscribeServer["tls"]): boolean {
  return value === true || value === 1 || value === "1" || value === "true";
}
