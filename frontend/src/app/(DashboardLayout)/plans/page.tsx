"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Grid,
  Radio,
  RadioGroup,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import {
  IconBolt,
  IconCheck,
  IconCreditCard,
  IconDeviceDesktop,
  IconExternalLink,
  IconRefresh,
  IconShoppingCart,
} from "@tabler/icons-react";

import PageContainer from "@/app/(DashboardLayout)/components/container/PageContainer";
import { formatBytes, formatMoney } from "@/lib/format";
import { cancelOrder, checkoutOrder, createOrder, getOrderDetail } from "@/services/order.service";
import { getPlansPageData, type PlansPageData } from "@/services/plans.service";
import type { OrderDetail, PaymentMethod, PaymentResult, PlanPeriodKey, PlanPublic } from "@/types/api";

type SelectedPeriod = {
  plan: PlanPublic;
  key: PlanPeriodKey;
  label: string;
  price: number;
};

type CheckoutState = {
  tradeNo: string;
  order: OrderDetail;
  result: PaymentResult;
};

const PERIOD_OPTIONS: Array<{ key: PlanPeriodKey; label: string; description: string }> = [
  { key: "month_price", label: "月付", description: "1 个月" },
  { key: "quarter_price", label: "季付", description: "3 个月" },
  { key: "half_year_price", label: "半年付", description: "6 个月" },
  { key: "year_price", label: "年付", description: "12 个月" },
  { key: "two_year_price", label: "两年付", description: "24 个月" },
  { key: "three_year_price", label: "三年付", description: "36 个月" },
  { key: "onetime_price", label: "一次性", description: "长期有效" },
  { key: "reset_price", label: "重置流量", description: "当前套餐" },
];

export default function PlansPage() {
  const [data, setData] = useState<PlansPageData | null>(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<SelectedPeriod | null>(null);
  const [couponCode, setCouponCode] = useState("");
  const [paymentId, setPaymentId] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [checkout, setCheckout] = useState<CheckoutState | null>(null);

  const currencySymbol = data?.config.currency_symbol || "¥";

  const loadPlans = async () => {
    setError("");
    try {
      const nextData = await getPlansPageData();
      setData(nextData);
      setPaymentId(nextData.payments[0]?.id || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "套餐加载失败");
    }
  };

  useEffect(() => {
    let cancelled = false;
    getPlansPageData()
      .then((nextData) => {
        if (!cancelled) {
          setData(nextData);
          setPaymentId(nextData.payments[0]?.id || 0);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "套餐加载失败");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const sortedPlans = useMemo(() => {
    return [...(data?.plans || [])].sort((left, right) => (left.sort || 0) - (right.sort || 0));
  }, [data]);

  const openCheckout = (period: SelectedPeriod) => {
    setSelected(period);
    setCouponCode("");
    setCheckout(null);
    setError("");
    setPaymentId(data?.payments[0]?.id || 0);
  };

  const closeCheckout = () => {
    if (submitting) {
      return;
    }
    setSelected(null);
    setCheckout(null);
    setCouponCode("");
  };

  const submitOrder = async () => {
    if (!selected) {
      return;
    }

    setSubmitting(true);
    setError("");
    setCheckout(null);
    try {
      const tradeNo = await createOrder({
        planId: selected.plan.id,
        period: selected.key,
        couponCode: couponCode.trim() || undefined,
      });
      const detail = await getOrderDetail(tradeNo);

      if (detail.order.total_amount > 0 && !paymentId) {
        await cancelOrder(tradeNo);
        throw new Error("暂无可用支付方式，订单已自动取消");
      }

      const result = await checkoutOrder(tradeNo, detail.order.total_amount > 0 ? paymentId : 0);
      setCheckout({ tradeNo, order: detail, result });
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建订单失败");
    } finally {
      setSubmitting(false);
    }
  };

  const openPayment = () => {
    if (typeof checkout?.result.data !== "string" || !checkout.result.data) {
      return;
    }
    window.open(checkout.result.data, "_blank", "noopener,noreferrer");
  };

  if (!data && !error) {
    return <PlansSkeleton />;
  }

  return (
    <PageContainer title="购买套餐" description="浏览套餐、创建订单并完成支付">
      <Stack spacing={3}>
        <Box>
          <Typography variant="h3">购买套餐</Typography>
          <Typography variant="body1" color="text.secondary" mt={0.5}>
            当前套餐为 {data?.subscribe.plan?.name || "暂无套餐"}，可按需新购、续费、变更或重置流量。
          </Typography>
        </Box>

        {error ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={() => void loadPlans()}>
                重试
              </Button>
            }
          >
            {error}
          </Alert>
        ) : null}

        {data ? (
          <Grid container spacing={3}>
            {sortedPlans.length ? (
              sortedPlans.map((plan) => (
                <Grid key={plan.id} size={{ xs: 12, lg: 6, xl: 4 }}>
                  <PlanCard
                    plan={plan}
                    currentPlanId={data.subscribe.plan_id || null}
                    currencySymbol={currencySymbol}
                    onSelect={openCheckout}
                  />
                </Grid>
              ))
            ) : (
              <Grid size={{ xs: 12 }}>
                <Card elevation={9}>
                  <CardContent>
                    <Typography color="text.secondary">暂无可购买套餐</Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        ) : null}
      </Stack>

      <Dialog open={Boolean(selected)} onClose={closeCheckout} fullWidth maxWidth="sm">
        <DialogTitle>{checkout ? "订单结账" : "确认订单"}</DialogTitle>
        <DialogContent>
          {selected ? (
            <Stack spacing={2} mt={0.5}>
              <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
                <Box>
                  <Typography variant="h6">{selected.plan.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selected.label} · {formatBytes(selected.plan.transfer_enable)}
                  </Typography>
                </Box>
                <Typography variant="h5">{formatMoney(selected.price, currencySymbol)}</Typography>
              </Stack>

              {!checkout ? (
                <>
                  <TextField
                    label="优惠码"
                    value={couponCode}
                    onChange={(event) => setCouponCode(event.target.value)}
                    fullWidth
                  />

                  <Box>
                    <Typography variant="subtitle2" mb={1}>
                      支付方式
                    </Typography>
                    {data?.payments.length ? (
                      <RadioGroup
                        value={String(paymentId)}
                        onChange={(event) => setPaymentId(Number(event.target.value))}
                      >
                        {data.payments.map((payment) => (
                          <FormControlLabel
                            key={payment.id}
                            value={String(payment.id)}
                            control={<Radio />}
                            label={<PaymentLabel payment={payment} currencySymbol={currencySymbol} />}
                          />
                        ))}
                      </RadioGroup>
                    ) : (
                      <Alert severity="warning">暂无可用支付方式；如果余额足够，零元订单仍可直接完成。</Alert>
                    )}
                  </Box>
                </>
              ) : (
                <CheckoutResultView checkout={checkout} currencySymbol={currencySymbol} />
              )}
            </Stack>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeCheckout} disabled={submitting}>
            关闭
          </Button>
          {checkout?.result.type === 1 ? (
            <Button variant="contained" startIcon={<IconExternalLink size={18} />} onClick={openPayment}>
              打开支付
            </Button>
          ) : null}
          {!checkout ? (
            <Button
              variant="contained"
              startIcon={<IconCreditCard size={18} />}
              disabled={submitting}
              onClick={() => void submitOrder()}
            >
              {submitting ? "处理中" : "创建并结账"}
            </Button>
          ) : null}
        </DialogActions>
      </Dialog>
    </PageContainer>
  );
}

function PlanCard({
  plan,
  currentPlanId,
  currencySymbol,
  onSelect,
}: {
  plan: PlanPublic;
  currentPlanId: number | null;
  currencySymbol: string;
  onSelect: (period: SelectedPeriod) => void;
}) {
  const periods = availablePeriods(plan, currentPlanId);
  const soldOut = plan.capacity_limit !== null && plan.capacity_limit !== undefined && plan.capacity_limit <= 0;
  const isCurrent = currentPlanId === plan.id;

  return (
    <Card elevation={9} sx={{ height: "100%" }}>
      <CardContent sx={{ height: "100%" }}>
        <Stack spacing={2.5} height="100%">
          <Stack spacing={1}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1}>
              <Typography variant="h4">{plan.name}</Typography>
              <Stack direction="row" spacing={0.75}>
                {isCurrent ? <Chip size="small" color="primary" label="当前套餐" /> : null}
                {soldOut ? <Chip size="small" color="warning" label="已售罄" /> : null}
              </Stack>
            </Stack>
            <Typography variant="body2" color="text.secondary">
              {formatPlanSummary(plan)}
            </Typography>
          </Stack>

          <Grid container spacing={1.5}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <PlanMetric icon={<IconBolt size={18} />} label="流量" value={formatBytes(plan.transfer_enable)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <PlanMetric
                icon={<IconDeviceDesktop size={18} />}
                label="设备"
                value={plan.device_limit ? `${plan.device_limit}` : "不限"}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <PlanMetric
                icon={<IconRefresh size={18} />}
                label="速度"
                value={plan.speed_limit ? `${plan.speed_limit} Mbps` : "不限"}
              />
            </Grid>
          </Grid>

          <Stack spacing={1} flex={1}>
            {planFeatures(plan).map((feature) => (
              <Stack key={feature} direction="row" spacing={1} alignItems="center">
                <IconCheck size={16} />
                <Typography variant="body2">{feature}</Typography>
              </Stack>
            ))}
          </Stack>

          <Divider />

          <Grid container spacing={1}>
            {periods.length ? (
              periods.map((period) => (
                <Grid key={period.key} size={{ xs: 12, sm: 6 }}>
                  <Button
                    variant={period.key === "reset_price" ? "outlined" : "contained"}
                    color={period.key === "reset_price" ? "secondary" : "primary"}
                    fullWidth
                    disabled={soldOut && period.key !== "reset_price"}
                    startIcon={<IconShoppingCart size={18} />}
                    onClick={() => onSelect({ plan, key: period.key, label: period.label, price: period.price })}
                    sx={{ justifyContent: "space-between", minHeight: 48 }}
                  >
                    <span>{period.label}</span>
                    <span>{formatMoney(period.price, currencySymbol)}</span>
                  </Button>
                </Grid>
              ))
            ) : (
              <Grid size={{ xs: 12 }}>
                <Button fullWidth variant="outlined" disabled>
                  暂不可购买
                </Button>
              </Grid>
            )}
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
}

function PlanMetric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <Stack
      spacing={0.75}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        px: 1.25,
        py: 1,
        minHeight: 74,
      }}
    >
      <Stack direction="row" spacing={0.75} alignItems="center" color="text.secondary">
        {icon}
        <Typography variant="caption">{label}</Typography>
      </Stack>
      <Typography variant="subtitle2">{value}</Typography>
    </Stack>
  );
}

function PaymentLabel({ payment, currencySymbol }: { payment: PaymentMethod; currencySymbol: string }) {
  const fees = [
    payment.handling_fee_fixed ? `固定 ${formatMoney(payment.handling_fee_fixed, currencySymbol)}` : "",
    payment.handling_fee_percent ? `${payment.handling_fee_percent}%` : "",
  ].filter(Boolean);

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Typography variant="body2">{payment.name}</Typography>
      <Typography variant="caption" color="text.secondary">
        {fees.length ? `手续费 ${fees.join(" + ")}` : payment.payment}
      </Typography>
    </Stack>
  );
}

function CheckoutResultView({ checkout, currencySymbol }: { checkout: CheckoutState; currencySymbol: string }) {
  const { order } = checkout.order;
  const result = checkout.result;

  if (result.type === -1) {
    return <Alert severity="success">订单已完成，套餐已开通。</Alert>;
  }

  return (
    <Stack spacing={2}>
      <Alert severity="info">
        订单 {checkout.tradeNo} 已创建，应付 {formatMoney(order.total_amount, currencySymbol)}。
      </Alert>
      {result.type === 0 && typeof result.data === "string" ? (
        <Box
          sx={{
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 1,
            p: 2,
            textAlign: "center",
          }}
        >
          {isImageLike(result.data) ? (
            <Box component="img" src={result.data} alt="支付二维码" sx={{ maxWidth: 220, width: "100%" }} />
          ) : (
            <Typography variant="body2" sx={{ wordBreak: "break-all" }}>
              {result.data}
            </Typography>
          )}
        </Box>
      ) : null}
      {result.type === 1 ? <Alert severity="success">支付链接已生成，请打开后完成付款。</Alert> : null}
    </Stack>
  );
}

function PlansSkeleton() {
  return (
    <Stack spacing={3}>
      <Skeleton variant="rounded" height={80} />
      <Grid container spacing={3}>
        {[1, 2, 3].map((item) => (
          <Grid key={item} size={{ xs: 12, lg: 6, xl: 4 }}>
            <Skeleton variant="rounded" height={420} />
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}

function availablePeriods(plan: PlanPublic, currentPlanId: number | null) {
  return PERIOD_OPTIONS.map((period) => ({
    ...period,
    price: plan[period.key],
  })).filter((period): period is { key: PlanPeriodKey; label: string; description: string; price: number } => {
    if (period.price === null || period.price === undefined || period.price < 0) {
      return false;
    }
    if (period.key === "reset_price" && currentPlanId !== plan.id) {
      return false;
    }
    return true;
  });
}

function planFeatures(plan: PlanPublic): string[] {
  const content = stripTags(plan.content || "")
    .split(/\r?\n|；|;/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 4);

  if (content.length) {
    return content;
  }

  return [
    `${formatBytes(plan.transfer_enable)} 可用流量`,
    plan.device_limit ? `${plan.device_limit} 台设备在线` : "设备数量不限",
    plan.speed_limit ? `${plan.speed_limit} Mbps 速率限制` : "速率不限",
  ];
}

function formatPlanSummary(plan: PlanPublic): string {
  const capacity =
    plan.capacity_limit === null || plan.capacity_limit === undefined ? "不限容量" : `剩余 ${plan.capacity_limit} 位`;
  return `${capacity} · ${formatBytes(plan.transfer_enable)} 流量`;
}

function stripTags(value: string): string {
  return value.replace(/<[^>]*>/g, "\n");
}

function isImageLike(value: string): boolean {
  return /^https?:\/\//.test(value) || value.startsWith("data:image/");
}
