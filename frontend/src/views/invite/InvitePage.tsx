"use client";

import {
  Alert,
  Box,
  Button,
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material/Select";
import { IconCash, IconCopy, IconGift, IconPlus, IconRefresh, IconSend, IconUsers } from "@tabler/icons-react";
import type { FormEvent, ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import CustomTextField from "@/components/forms/CustomTextField";
import PageContainer from "@/components/layout/PageContainer";
import { useSiteConfig } from "@/contexts/SiteConfigContext";
import { formatDateTime, formatMoney } from "@/lib/format";
import { getCommonConfig } from "@/services/common.service";
import { createInviteCode, getCommissionLogs, getInviteOverview, transferCommission } from "@/services/invite.service";
import { createWithdrawTicket } from "@/services/ticket.service";
import type { CommissionLog, CommonConfig, InviteCode, InviteOverview } from "@/types/api";

const WITHDRAW_METHOD_LABELS: Record<string, string> = {
  alipay: "支付宝",
  bank: "银行卡",
  usdt: "USDT",
};

export default function InvitePage() {
  const { appUrl } = useSiteConfig();
  const [overview, setOverview] = useState<InviteOverview | null>(null);
  const [logs, setLogs] = useState<CommissionLog[]>([]);
  const [config, setConfig] = useState<CommonConfig>({});
  const [transferAmount, setTransferAmount] = useState("");
  const [withdrawMethod, setWithdrawMethod] = useState("");
  const [withdrawAccount, setWithdrawAccount] = useState("");
  const [copied, setCopied] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [creatingCode, setCreatingCode] = useState(false);
  const [transferring, setTransferring] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);

  const stat = overview?.stat || [0, 0, 0, 0, 0];
  const registeredCount = stat[0];
  const paidCommission = stat[1];
  const pendingCommission = stat[2];
  const commissionRate = stat[3];
  const commissionBalance = stat[4];
  const currencySymbol = config.currency_symbol || "¥";
  const inviteLimit = config.invite_gen_limit ?? 5;
  const withdrawLimit = (config.commission_withdraw_limit ?? 100) * 100;
  const withdrawMethods = config.withdraw_methods || [];
  const canCreateCode = (overview?.codes.length || 0) < inviteLimit;
  const transferAmountCents = useMemo(() => parseMoneyToCents(transferAmount), [transferAmount]);
  const canTransfer = transferAmountCents > 0 && transferAmountCents <= commissionBalance;
  const canWithdraw =
    !config.withdraw_close &&
    withdrawMethods.length > 0 &&
    commissionBalance >= withdrawLimit &&
    withdrawMethod &&
    withdrawAccount.trim();

  const loadInvite = async () => {
    setError("");
    setLoading(true);
    try {
      const [nextOverview, nextLogs, nextConfig] = await Promise.all([
        getInviteOverview(),
        getCommissionLogs(),
        getCommonConfig(),
      ]);
      setOverview(nextOverview);
      setLogs(nextLogs);
      setConfig(nextConfig);
      setWithdrawMethod(nextConfig.withdraw_methods?.[0] || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "邀请返佣加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadInvite();
  }, []);

  const createCode = async () => {
    setError("");
    setSuccess("");
    setCreatingCode(true);
    try {
      await createInviteCode();
      setSuccess("邀请码已生成");
      await loadInvite();
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成邀请码失败");
    } finally {
      setCreatingCode(false);
    }
  };

  const submitTransfer = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!canTransfer) {
      setError("请输入不超过可用佣金的划转金额");
      return;
    }
    setTransferring(true);
    try {
      await transferCommission(transferAmountCents);
      setTransferAmount("");
      setSuccess("佣金已划转到账户余额");
      await loadInvite();
    } catch (err) {
      setError(err instanceof Error ? err.message : "佣金划转失败");
    } finally {
      setTransferring(false);
    }
  };

  const submitWithdraw = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!canWithdraw) {
      setError("当前不满足提现申请条件");
      return;
    }
    setWithdrawing(true);
    try {
      await createWithdrawTicket({ withdrawMethod, withdrawAccount });
      setWithdrawAccount("");
      setSuccess("提现申请已提交为工单");
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交提现申请失败");
    } finally {
      setWithdrawing(false);
    }
  };

  const copyText = async (key: string, value: string) => {
    await navigator.clipboard.writeText(value);
    setCopied(key);
    window.setTimeout(() => setCopied(""), 1800);
  };

  if (loading && !overview) {
    return <InviteSkeleton />;
  }

  return (
    <PageContainer title="邀请返佣" description="管理邀请码、查看佣金明细并发起佣金操作">
      <Stack spacing={3}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography variant="h3">邀请返佣</Typography>
            <Typography variant="body1" color="text.secondary" mt={0.5}>
              生成邀请码、跟踪返佣入账，并处理佣金余额。
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<IconRefresh size={18} />} onClick={() => void loadInvite()}>
            刷新
          </Button>
        </Stack>

        {error ? <Alert severity="error">{error}</Alert> : null}
        {success ? <Alert severity="success">{success}</Alert> : null}

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <MetricCard
              title="已邀请用户"
              value={`${registeredCount}`}
              subtitle={`返佣比例 ${commissionRate}%`}
              icon={<IconUsers size={22} />}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <MetricCard
              title="已入账佣金"
              value={formatMoney(paidCommission, currencySymbol)}
              subtitle="历史累计"
              icon={<IconGift size={22} />}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <MetricCard
              title="待确认佣金"
              value={formatMoney(pendingCommission, currencySymbol)}
              subtitle="订单确认后入账"
              icon={<IconRefresh size={22} />}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6, lg: 3 }}>
            <MetricCard
              title="可用佣金"
              value={formatMoney(commissionBalance, currencySymbol)}
              subtitle={`最低提现 ${formatMoney(withdrawLimit, currencySymbol)}`}
              icon={<IconCash size={22} />}
            />
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, lg: 7 }}>
            <Card elevation={9}>
              <CardContent>
                <Stack spacing={3}>
                  <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={2}>
                    <SectionHeader title="邀请码" description={`最多可生成 ${inviteLimit} 个有效邀请码。`} />
                    <Button
                      variant="contained"
                      startIcon={<IconPlus size={18} />}
                      onClick={() => void createCode()}
                      disabled={!canCreateCode || creatingCode}
                    >
                      {creatingCode ? "生成中..." : "生成邀请码"}
                    </Button>
                  </Stack>

                  {overview?.codes.length ? (
                    <Stack spacing={1.5}>
                      {overview.codes.map((code) => (
                        <InviteCodeItem
                          code={code}
                          link={buildInviteLink(appUrl, code.code)}
                          copied={copied}
                          onCopy={copyText}
                          key={code.id}
                        />
                      ))}
                    </Stack>
                  ) : (
                    <Box py={4} textAlign="center">
                      <Typography color="text.secondary">暂无邀请码</Typography>
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, lg: 5 }}>
            <Stack spacing={3}>
              <Card elevation={9}>
                <CardContent>
                  <Stack spacing={3}>
                    <SectionHeader title="佣金划转" description="将可用佣金转入账户余额，用于购买套餐或续费。" />
                    <Box component="form" onSubmit={submitTransfer}>
                      <Stack spacing={2}>
                        <CustomTextField
                          label="划转金额"
                          value={transferAmount}
                          onChange={(event) => setTransferAmount(event.target.value)}
                          placeholder="例如 10.00"
                          required
                          fullWidth
                        />
                        <Button
                          type="submit"
                          variant="contained"
                          startIcon={<IconSend size={18} />}
                          disabled={!canTransfer || transferring}
                        >
                          {transferring ? "划转中..." : "划转到余额"}
                        </Button>
                      </Stack>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>

              <Card elevation={9}>
                <CardContent>
                  <Stack spacing={3}>
                    <SectionHeader title="佣金提现" description="提交后会创建一条提现工单，等待人工处理。" />
                    {config.withdraw_close ? <Alert severity="warning">当前站点已关闭佣金提现。</Alert> : null}
                    {commissionBalance < withdrawLimit ? (
                      <Alert severity="info">
                        可用佣金达到 {formatMoney(withdrawLimit, currencySymbol)} 后可申请提现。
                      </Alert>
                    ) : null}
                    <Box component="form" onSubmit={submitWithdraw}>
                      <Stack spacing={2}>
                        <FormControl fullWidth disabled={Boolean(config.withdraw_close || !withdrawMethods.length)}>
                          <InputLabel id="withdraw-method-label">提现方式</InputLabel>
                          <Select
                            labelId="withdraw-method-label"
                            label="提现方式"
                            value={withdrawMethod}
                            onChange={(event: SelectChangeEvent) => setWithdrawMethod(event.target.value)}
                          >
                            {withdrawMethods.map((method) => (
                              <MenuItem value={method} key={method}>
                                {WITHDRAW_METHOD_LABELS[method] || method}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                        <CustomTextField
                          label="提现账号"
                          value={withdrawAccount}
                          onChange={(event) => setWithdrawAccount(event.target.value)}
                          required
                          fullWidth
                          disabled={Boolean(config.withdraw_close)}
                        />
                        <Button
                          type="submit"
                          variant="outlined"
                          startIcon={<IconSend size={18} />}
                          disabled={!canWithdraw || withdrawing}
                        >
                          {withdrawing ? "提交中..." : "提交提现申请"}
                        </Button>
                      </Stack>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Card elevation={9}>
              <CardContent>
                <Stack spacing={2}>
                  <SectionHeader title="佣金明细" description="展示已入账的订单返佣记录。" />
                  {logs.length ? (
                    <Box sx={{ overflowX: "auto" }}>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>订单号</TableCell>
                            <TableCell>订单金额</TableCell>
                            <TableCell>返佣金额</TableCell>
                            <TableCell>时间</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {logs.map((log) => (
                            <TableRow key={log.id} hover>
                              <TableCell>{log.trade_no}</TableCell>
                              <TableCell>{formatMoney(log.order_amount, currencySymbol)}</TableCell>
                              <TableCell>{formatMoney(log.get_amount, currencySymbol)}</TableCell>
                              <TableCell>{formatDateTime(log.created_at)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Box>
                  ) : (
                    <Box py={4} textAlign="center">
                      <Typography color="text.secondary">暂无佣金记录</Typography>
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Stack>
    </PageContainer>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: ReactNode;
}) {
  return (
    <Card elevation={9}>
      <CardContent>
        <Stack direction="row" spacing={2} alignItems="center">
          <Box color="primary.main">{icon}</Box>
          <Box minWidth={0}>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
            <Typography variant="h4">{value}</Typography>
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <Box>
      <Typography variant="h5">{title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
    </Box>
  );
}

function InviteCodeItem({
  code,
  link,
  copied,
  onCopy,
}: {
  code: InviteCode;
  link: string;
  copied: string;
  onCopy: (key: string, value: string) => Promise<void>;
}) {
  return (
    <Box sx={{ border: "1px solid", borderColor: "divider", borderRadius: 2, p: 2 }}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} justifyContent="space-between">
        <Box minWidth={0}>
          <Stack direction="row" spacing={1} alignItems="center" mb={0.75}>
            <Typography variant="h5" letterSpacing={1}>
              {code.code}
            </Typography>
            <Chip
              size="small"
              color={code.status === 0 ? "success" : "default"}
              label={code.status === 0 ? "有效" : "已使用"}
            />
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ wordBreak: "break-all" }}>
            {link}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            访问 {code.pv} 次 · {formatDateTime(code.created_at)}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1} flexShrink={0}>
          <Button
            variant="outlined"
            startIcon={<IconCopy size={16} />}
            onClick={() => void onCopy(`code-${code.id}`, code.code)}
          >
            {copied === `code-${code.id}` ? "已复制" : "复制码"}
          </Button>
          <Button
            variant="contained"
            startIcon={<IconCopy size={16} />}
            onClick={() => void onCopy(`link-${code.id}`, link)}
          >
            {copied === `link-${code.id}` ? "已复制" : "复制链接"}
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}

function InviteSkeleton() {
  return (
    <PageContainer title="邀请返佣" description="管理邀请码、查看佣金明细并发起佣金操作">
      <Stack spacing={3}>
        <Box>
          <Skeleton width={160} height={42} />
          <Skeleton width={320} />
        </Box>
        <Grid container spacing={3}>
          {[0, 1, 2, 3].map((item) => (
            <Grid size={{ xs: 12, md: 6, lg: 3 }} key={item}>
              <Card elevation={9}>
                <CardContent>
                  <Skeleton width="55%" />
                  <Skeleton height={42} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        <Card elevation={9}>
          <CardContent>
            <Skeleton height={220} />
          </CardContent>
        </Card>
      </Stack>
    </PageContainer>
  );
}

function buildInviteLink(appUrl: string, code: string): string {
  const origin = (appUrl || (typeof window !== "undefined" ? window.location.origin : "")).replace(/\/$/, "");
  const path = `/auth/register?invite_code=${encodeURIComponent(code)}`;
  return origin ? `${origin}${path}` : path;
}

function parseMoneyToCents(value: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return 0;
  }
  return Math.round(parsed * 100);
}
