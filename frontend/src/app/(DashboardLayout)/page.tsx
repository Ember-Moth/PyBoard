"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
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
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  IconCopy,
  IconCreditCard,
  IconHeadset,
  IconKey,
  IconRefresh,
  IconServer,
  IconShare3,
} from "@tabler/icons-react";

import PageContainer from "@/app/(DashboardLayout)/components/container/PageContainer";
import { formatBytes, formatDateTime, formatMoney, percent } from "@/lib/format";
import { getDashboardData, type DashboardData } from "@/services/dashboard.service";
import { resetUserSecurity } from "@/services/user.service";

const Dashboard = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [resetting, setResetting] = useState(false);

  const loadDashboard = async () => {
    setError("");
    try {
      setData(await getDashboardData());
    } catch (err) {
      setError(err instanceof Error ? err.message : "仪表盘加载失败");
    }
  };

  useEffect(() => {
    let cancelled = false;
    getDashboardData()
      .then((nextData) => {
        if (!cancelled) {
          setData(nextData);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "仪表盘加载失败");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const usage = useMemo(() => {
    if (!data) {
      return { used: 0, total: 0, value: 0 };
    }
    const used = (data.subscribe.u || 0) + (data.subscribe.d || 0);
    return {
      used,
      total: data.subscribe.transfer_enable || 0,
      value: percent(used, data.subscribe.transfer_enable || 0),
    };
  }, [data]);

  const status = useMemo(() => {
    if (!data) {
      return { label: "加载中", color: "default" as const, message: "" };
    }
    const expiredAt = data.subscribe.expired_at || 0;
    const expired = expiredAt > 0 && expiredAt <= data.now;
    if (data.profile.banned) {
      return { label: "已封禁", color: "error" as const, message: "账户已被封禁，请联系支持。" };
    }
    if (!data.subscribe.plan) {
      return { label: "未购套餐", color: "warning" as const, message: "购买套餐后即可生成订阅并使用节点。" };
    }
    if (expired) {
      return { label: "已过期", color: "warning" as const, message: "套餐已过期，请续费或购买新套餐。" };
    }
    if (usage.total > 0 && usage.used >= usage.total) {
      return { label: "流量用尽", color: "warning" as const, message: "可续费、变更套餐或等待下次流量重置。" };
    }
    return { label: "正常", color: "success" as const, message: "账户状态正常，订阅可用。" };
  }, [data, usage]);

  const copySubscribeUrl = async () => {
    if (!data?.subscribe.subscribe_url) {
      return;
    }
    await navigator.clipboard.writeText(data.subscribe.subscribe_url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const resetSecurity = async () => {
    setResetting(true);
    setError("");
    try {
      await resetUserSecurity();
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置订阅失败");
    } finally {
      setResetting(false);
    }
  };

  if (!data && !error) {
    return <DashboardSkeleton />;
  }

  return (
    <PageContainer title="用户仪表盘" description="账户概览、订阅和流量状态">
      <Stack spacing={3}>
        <Box>
          <Typography variant="h3">用户仪表盘</Typography>
          <Typography variant="body1" color="text.secondary" mt={0.5}>
            查看套餐、流量、订阅和近期账户动态。
          </Typography>
        </Box>

        {error ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={() => void loadDashboard()}>
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
                <Stack direction={{ xs: "column", md: "row" }} spacing={3} justifyContent="space-between">
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
                    <Button component={Link} href="/plans" variant="contained" startIcon={<IconCreditCard size={18} />}>
                      购买套餐
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<IconCopy size={18} />}
                      onClick={() => void copySubscribeUrl()}
                      disabled={!data.subscribe.subscribe_url}
                    >
                      {copied ? "已复制" : "复制订阅"}
                    </Button>
                    <Button
                      variant="outlined"
                      color="secondary"
                      startIcon={<IconRefresh size={18} />}
                      onClick={() => void resetSecurity()}
                      disabled={resetting}
                    >
                      重置订阅
                    </Button>
                  </Stack>
                </Stack>
              </CardContent>
            </Card>

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6, lg: 3 }}>
                <MetricCard
                  title="已用流量"
                  value={formatBytes(usage.used)}
                  subtitle={`总量 ${formatBytes(usage.total)}`}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6, lg: 3 }}>
                <MetricCard
                  title="到期时间"
                  value={formatDateTime(data.subscribe.expired_at)}
                  subtitle={`重置剩余 ${data.subscribe.reset_day || 0} 天`}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6, lg: 3 }}>
                <MetricCard
                  title="账户余额"
                  value={formatMoney(data.profile.balance, data.config.currency_symbol)}
                  subtitle={`佣金 ${formatMoney(data.profile.commission_balance, data.config.currency_symbol)}`}
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

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, lg: 8 }}>
                <Card elevation={9}>
                  <CardContent>
                    <Stack spacing={2}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="h5">流量使用</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {usage.value}%
                        </Typography>
                      </Stack>
                      <LinearProgress variant="determinate" value={usage.value} sx={{ height: 10, borderRadius: 5 }} />
                      <Grid container spacing={2}>
                        <Grid size={{ xs: 12, sm: 4 }}>
                          <TrafficValue label="上传" value={formatBytes(data.subscribe.u)} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 4 }}>
                          <TrafficValue label="下载" value={formatBytes(data.subscribe.d)} />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 4 }}>
                          <TrafficValue label="剩余" value={formatBytes(Math.max(usage.total - usage.used, 0))} />
                        </Grid>
                      </Grid>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, lg: 4 }}>
                <Card elevation={9}>
                  <CardContent>
                    <Typography variant="h5" mb={2}>
                      账户角标
                    </Typography>
                    <Stack spacing={1.5}>
                      <StatRow label="待支付订单" value={data.stats[0] || 0} />
                      <StatRow label="开启工单" value={data.stats[1] || 0} />
                      <StatRow label="邀请人数" value={data.stats[2] || 0} />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Grid container spacing={3}>
              <Grid size={{ xs: 12, lg: 7 }}>
                <Card elevation={9}>
                  <CardContent>
                    <Typography variant="h5" mb={2}>
                      快捷操作
                    </Typography>
                    <Grid container spacing={2}>
                      <QuickAction
                        href="/subscribe"
                        icon={<IconKey size={20} />}
                        title="订阅管理"
                        subtitle="复制链接、查看节点"
                      />
                      <QuickAction
                        href="/plans"
                        icon={<IconCreditCard size={20} />}
                        title="购买套餐"
                        subtitle="续费或更换套餐"
                      />
                      <QuickAction
                        href="/tickets"
                        icon={<IconHeadset size={20} />}
                        title="工单支持"
                        subtitle="提交问题与反馈"
                      />
                      <QuickAction
                        href="/invite"
                        icon={<IconShare3 size={20} />}
                        title="邀请返佣"
                        subtitle="查看邀请码和佣金"
                      />
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, lg: 5 }}>
                <Card elevation={9}>
                  <CardContent>
                    <Typography variant="h5" mb={2}>
                      最新公告
                    </Typography>
                    <Stack spacing={1.5}>
                      {data.notices.items.length ? (
                        data.notices.items.map((notice) => (
                          <Box key={notice.id}>
                            <Typography variant="subtitle2">{notice.title}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatDateTime(notice.created_at)}
                            </Typography>
                          </Box>
                        ))
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          暂无公告
                        </Typography>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Card elevation={9}>
              <CardContent>
                <Typography variant="h5" mb={2}>
                  最近流量记录
                </Typography>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>记录时间</TableCell>
                      <TableCell>节点</TableCell>
                      <TableCell>上传</TableCell>
                      <TableCell>下载</TableCell>
                      <TableCell>倍率</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.trafficLogs.length ? (
                      data.trafficLogs.map((item) => (
                        <TableRow key={`${item.server_id}-${item.record_at}`}>
                          <TableCell>{formatDateTime(item.record_at)}</TableCell>
                          <TableCell>
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <IconServer size={16} />
                              <span>{item.server_id}</span>
                            </Stack>
                          </TableCell>
                          <TableCell>{formatBytes(item.u)}</TableCell>
                          <TableCell>{formatBytes(item.d)}</TableCell>
                          <TableCell>{item.server_rate}</TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          暂无流量记录
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        ) : null}
      </Stack>
    </PageContainer>
  );
};

function DashboardSkeleton() {
  return (
    <Stack spacing={3}>
      <Skeleton variant="rounded" height={120} />
      <Grid container spacing={3}>
        {[1, 2, 3, 4].map((item) => (
          <Grid key={item} size={{ xs: 12, md: 6, lg: 3 }}>
            <Skeleton variant="rounded" height={130} />
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

function TrafficValue({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6">{value}</Typography>
    </Box>
  );
}

function StatRow({ label, value }: { label: string; value: number }) {
  return (
    <Stack direction="row" justifyContent="space-between">
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="subtitle2">{value}</Typography>
    </Stack>
  );
}

function QuickAction({
  href,
  icon,
  title,
  subtitle,
}: {
  href: string;
  icon: ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <Grid size={{ xs: 12, sm: 6 }}>
      <Button
        component={Link}
        href={href}
        variant="outlined"
        fullWidth
        startIcon={icon}
        sx={{ justifyContent: "flex-start", py: 1.5, textAlign: "left" }}
      >
        <Box>
          <Typography variant="subtitle2">{title}</Typography>
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        </Box>
      </Button>
    </Grid>
  );
}

export default Dashboard;
