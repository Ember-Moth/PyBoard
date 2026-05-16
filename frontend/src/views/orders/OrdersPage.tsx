"use client";

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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { IconCreditCard, IconExternalLink, IconEye, IconRefresh, IconX } from "@tabler/icons-react";
import { useEffect, useMemo, useState } from "react";

import PageContainer from "@/components/layout/PageContainer";
import { formatDateTime, formatMoney } from "@/lib/format";
import { cancelOrder, checkOrderStatus, checkoutOrder, getOrderDetail } from "@/services/order.service";
import { getOrdersPageData, type OrdersPageData } from "@/services/orders.service";
import type { OrderDetail, OrderPublic, PaymentMethod, PaymentResult } from "@/types/api";

type StatusFilter = number | undefined;

type ActiveOrderState = {
  detail: OrderDetail;
  result: PaymentResult | null;
};

const STATUS_FILTERS: Array<{ label: string; value: StatusFilter }> = [
  { label: "全部", value: undefined },
  { label: "待支付", value: 0 },
  { label: "开通中", value: 1 },
  { label: "已取消", value: 2 },
  { label: "已完成", value: 3 },
];

const STATUS_META: Record<number, { label: string; color: "default" | "primary" | "success" | "warning" | "error" }> = {
  0: { label: "待支付", color: "warning" },
  1: { label: "开通中", color: "primary" },
  2: { label: "已取消", color: "default" },
  3: { label: "已完成", color: "success" },
  4: { label: "已折抵", color: "default" },
};

export default function OrdersPage() {
  const [data, setData] = useState<OrdersPageData | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>(undefined);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [activeOrder, setActiveOrder] = useState<ActiveOrderState | null>(null);
  const [paymentId, setPaymentId] = useState(0);
  const [loadingTradeNo, setLoadingTradeNo] = useState("");

  const currencySymbol = data?.config.currency_symbol || "¥";

  const loadOrders = async (nextStatus = statusFilter) => {
    setError("");
    try {
      const nextData = await getOrdersPageData(nextStatus);
      setData(nextData);
      setPaymentId(nextData.payments[0]?.id || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "订单加载失败");
    }
  };

  useEffect(() => {
    let cancelled = false;
    getOrdersPageData(statusFilter)
      .then((nextData) => {
        if (!cancelled) {
          setData(nextData);
          setPaymentId(nextData.payments[0]?.id || 0);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "订单加载失败");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [statusFilter]);

  const summary = useMemo(() => {
    const orders = data?.orders || [];
    return {
      pending: orders.filter((order) => order.status === 0).length,
      completed: orders.filter((order) => order.status === 3).length,
      totalAmount: orders.reduce((total, order) => total + (order.total_amount || 0), 0),
    };
  }, [data]);

  const changeStatusFilter = (nextStatus: StatusFilter) => {
    setStatusFilter(nextStatus);
    setMessage("");
    setError("");
  };

  const openOrder = async (order: OrderPublic) => {
    setLoadingTradeNo(order.trade_no);
    setError("");
    setMessage("");
    try {
      const detail = await getOrderDetail(order.trade_no);
      setActiveOrder({ detail, result: null });
      setPaymentId(data?.payments[0]?.id || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "订单详情加载失败");
    } finally {
      setLoadingTradeNo("");
    }
  };

  const submitCheckout = async () => {
    if (!activeOrder) {
      return;
    }

    const order = activeOrder.detail.order;
    if (order.total_amount > 0 && !paymentId) {
      setError("暂无可用支付方式");
      return;
    }

    setLoadingTradeNo(order.trade_no);
    setError("");
    try {
      const result = await checkoutOrder(order.trade_no, order.total_amount > 0 ? paymentId : 0);
      setActiveOrder({ ...activeOrder, result });
      if (result.type === -1) {
        setMessage("订单已完成，套餐已开通。");
        await loadOrders();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交支付失败");
    } finally {
      setLoadingTradeNo("");
    }
  };

  const cancelPendingOrder = async (order: OrderPublic) => {
    setLoadingTradeNo(order.trade_no);
    setError("");
    setMessage("");
    try {
      await cancelOrder(order.trade_no);
      setMessage("订单已取消。");
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "取消订单失败");
    } finally {
      setLoadingTradeNo("");
    }
  };

  const refreshOrderStatus = async (order: OrderPublic) => {
    setLoadingTradeNo(order.trade_no);
    setError("");
    setMessage("");
    try {
      const status = await checkOrderStatus(order.trade_no);
      setMessage(`订单状态：${statusLabel(status)}`);
      await loadOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "检查订单状态失败");
    } finally {
      setLoadingTradeNo("");
    }
  };

  const openPayment = () => {
    const value = activeOrder?.result?.data;
    if (typeof value !== "string" || !value) {
      return;
    }
    window.open(value, "_blank", "noopener,noreferrer");
  };

  if (!data && !error) {
    return <OrdersSkeleton />;
  }

  return (
    <PageContainer title="我的订单" description="查看订单流水、支付状态和订单详情">
      <Stack spacing={3}>
        <Box>
          <Typography variant="h3">我的订单</Typography>
          <Typography variant="body1" color="text.secondary" mt={0.5}>
            查看购买记录、继续支付待处理订单，或刷新支付状态。
          </Typography>
        </Box>

        {error ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={() => void loadOrders()}>
                重试
              </Button>
            }
          >
            {error}
          </Alert>
        ) : null}
        {message ? <Alert severity="success">{message}</Alert> : null}

        {data ? (
          <>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <MetricCard title="待支付" value={`${summary.pending}`} subtitle="需要继续处理的订单" />
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <MetricCard title="已完成" value={`${summary.completed}`} subtitle="已支付并完成开通" />
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <MetricCard
                  title="列表金额"
                  value={formatMoney(summary.totalAmount, currencySymbol)}
                  subtitle="当前筛选结果合计"
                />
              </Grid>
            </Grid>

            <Card elevation={9}>
              <CardContent>
                <Stack spacing={2}>
                  <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {STATUS_FILTERS.map((item) => (
                        <Button
                          key={item.label}
                          variant={statusFilter === item.value ? "contained" : "outlined"}
                          size="small"
                          onClick={() => changeStatusFilter(item.value)}
                        >
                          {item.label}
                        </Button>
                      ))}
                    </Stack>
                    <Button variant="outlined" startIcon={<IconRefresh size={18} />} onClick={() => void loadOrders()}>
                      刷新
                    </Button>
                  </Stack>

                  <TableContainer>
                    <Table sx={{ minWidth: 900 }}>
                      <TableHead>
                        <TableRow>
                          <TableCell>交易号</TableCell>
                          <TableCell>订单内容</TableCell>
                          <TableCell>金额</TableCell>
                          <TableCell>状态</TableCell>
                          <TableCell>创建时间</TableCell>
                          <TableCell>支付时间</TableCell>
                          <TableCell align="right">操作</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {data.orders.length ? (
                          data.orders.map((order) => (
                            <TableRow key={order.trade_no}>
                              <TableCell>
                                <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
                                  {order.trade_no}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Typography variant="subtitle2">
                                  {order.plan_id > 0 ? `套餐 #${order.plan_id}` : "余额充值"}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {periodLabel(order.period)}
                                </Typography>
                              </TableCell>
                              <TableCell>{formatMoney(order.total_amount, currencySymbol)}</TableCell>
                              <TableCell>
                                <Chip
                                  size="small"
                                  label={statusLabel(order.status)}
                                  color={statusColor(order.status)}
                                />
                              </TableCell>
                              <TableCell>{formatDateTime(order.created_at)}</TableCell>
                              <TableCell>{order.paid_at ? formatDateTime(order.paid_at) : "未支付"}</TableCell>
                              <TableCell align="right">
                                <Stack direction="row" spacing={1} justifyContent="flex-end">
                                  <Button
                                    size="small"
                                    variant="text"
                                    startIcon={<IconEye size={16} />}
                                    disabled={loadingTradeNo === order.trade_no}
                                    onClick={() => void openOrder(order)}
                                  >
                                    详情
                                  </Button>
                                  {order.status === 0 ? (
                                    <>
                                      <Button
                                        size="small"
                                        variant="contained"
                                        startIcon={<IconCreditCard size={16} />}
                                        disabled={loadingTradeNo === order.trade_no}
                                        onClick={() => void openOrder(order)}
                                      >
                                        支付
                                      </Button>
                                      <Button
                                        size="small"
                                        color="error"
                                        variant="outlined"
                                        startIcon={<IconX size={16} />}
                                        disabled={loadingTradeNo === order.trade_no}
                                        onClick={() => void cancelPendingOrder(order)}
                                      >
                                        取消
                                      </Button>
                                    </>
                                  ) : null}
                                  {order.status === 1 ? (
                                    <Button
                                      size="small"
                                      variant="outlined"
                                      startIcon={<IconRefresh size={16} />}
                                      disabled={loadingTradeNo === order.trade_no}
                                      onClick={() => void refreshOrderStatus(order)}
                                    >
                                      检查
                                    </Button>
                                  ) : null}
                                </Stack>
                              </TableCell>
                            </TableRow>
                          ))
                        ) : (
                          <TableRow>
                            <TableCell colSpan={7} align="center">
                              暂无订单
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

      <OrderDialog
        activeOrder={activeOrder}
        payments={data?.payments || []}
        paymentId={paymentId}
        currencySymbol={currencySymbol}
        loading={Boolean(activeOrder && loadingTradeNo === activeOrder.detail.order.trade_no)}
        onClose={() => setActiveOrder(null)}
        onPaymentChange={setPaymentId}
        onCheckout={() => void submitCheckout()}
        onOpenPayment={openPayment}
      />
    </PageContainer>
  );
}

function OrderDialog({
  activeOrder,
  payments,
  paymentId,
  currencySymbol,
  loading,
  onClose,
  onPaymentChange,
  onCheckout,
  onOpenPayment,
}: {
  activeOrder: ActiveOrderState | null;
  payments: PaymentMethod[];
  paymentId: number;
  currencySymbol: string;
  loading: boolean;
  onClose: () => void;
  onPaymentChange: (value: number) => void;
  onCheckout: () => void;
  onOpenPayment: () => void;
}) {
  const detail = activeOrder?.detail;
  const order = detail?.order;
  const result = activeOrder?.result;
  const canPay = Boolean(order && order.status === 0 && !result);

  return (
    <Dialog open={Boolean(activeOrder)} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>订单详情</DialogTitle>
      <DialogContent>
        {order ? (
          <Stack spacing={2} mt={0.5}>
            <Stack direction="row" justifyContent="space-between" spacing={2}>
              <Box>
                <Typography variant="h6">
                  {detail?.plan?.name || (order.plan_id > 0 ? `套餐 #${order.plan_id}` : "余额充值")}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {periodLabel(order.period)} · {order.trade_no}
                </Typography>
              </Box>
              <Chip size="small" label={statusLabel(order.status)} color={statusColor(order.status)} />
            </Stack>

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <InfoItem label="订单金额" value={formatMoney(order.total_amount, currencySymbol)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <InfoItem label="余额抵扣" value={formatMoney(order.balance_amount || 0, currencySymbol)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <InfoItem label="手续费" value={formatMoney(order.handling_amount || 0, currencySymbol)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <InfoItem label="创建时间" value={formatDateTime(order.created_at)} />
              </Grid>
            </Grid>

            {canPay ? (
              <>
                <Divider />
                <Box>
                  <Typography variant="subtitle2" mb={1}>
                    支付方式
                  </Typography>
                  {order.total_amount <= 0 ? (
                    <Alert severity="info">该订单无需在线支付，可直接提交结账。</Alert>
                  ) : payments.length ? (
                    <RadioGroup
                      value={String(paymentId)}
                      onChange={(event) => onPaymentChange(Number(event.target.value))}
                    >
                      {payments.map((payment) => (
                        <FormControlLabel
                          key={payment.id}
                          value={String(payment.id)}
                          control={<Radio />}
                          label={<PaymentLabel payment={payment} currencySymbol={currencySymbol} />}
                        />
                      ))}
                    </RadioGroup>
                  ) : (
                    <Alert severity="warning">暂无可用支付方式。</Alert>
                  )}
                </Box>
              </>
            ) : null}

            {result ? <PaymentResultView result={result} order={order} currencySymbol={currencySymbol} /> : null}
          </Stack>
        ) : null}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          关闭
        </Button>
        {result?.type === 1 ? (
          <Button variant="contained" startIcon={<IconExternalLink size={18} />} onClick={onOpenPayment}>
            打开支付
          </Button>
        ) : null}
        {canPay ? (
          <Button
            variant="contained"
            startIcon={<IconCreditCard size={18} />}
            disabled={loading || !order || (order.total_amount > 0 && !paymentId)}
            onClick={onCheckout}
          >
            {loading ? "提交中" : "提交支付"}
          </Button>
        ) : null}
      </DialogActions>
    </Dialog>
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

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="subtitle2">{value}</Typography>
    </Box>
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

function PaymentResultView({
  result,
  order,
  currencySymbol,
}: {
  result: PaymentResult;
  order: OrderPublic;
  currencySymbol: string;
}) {
  if (result.type === -1) {
    return <Alert severity="success">订单已完成，套餐已开通。</Alert>;
  }

  return (
    <Stack spacing={2}>
      <Alert severity="info">
        订单应付 {formatMoney(order.total_amount, currencySymbol)}。完成支付后可刷新订单状态。
      </Alert>
      {result.type === 0 && typeof result.data === "string" ? (
        <Box sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1, p: 2, textAlign: "center" }}>
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

function OrdersSkeleton() {
  return (
    <Stack spacing={3}>
      <Grid container spacing={3}>
        {[1, 2, 3].map((item) => (
          <Grid key={item} size={{ xs: 12, md: 4 }}>
            <Skeleton variant="rounded" height={120} />
          </Grid>
        ))}
      </Grid>
      <Skeleton variant="rounded" height={420} />
    </Stack>
  );
}

function statusLabel(status: number): string {
  return STATUS_META[status]?.label || "未知";
}

function statusColor(status: number) {
  return STATUS_META[status]?.color || "default";
}

function periodLabel(period: string): string {
  const labels: Record<string, string> = {
    month_price: "月付",
    quarter_price: "季付",
    half_year_price: "半年付",
    year_price: "年付",
    two_year_price: "两年付",
    three_year_price: "三年付",
    onetime_price: "一次性",
    reset_price: "重置流量",
    deposit: "余额充值",
  };
  return labels[period] || period;
}

function isImageLike(value: string): boolean {
  return /^https?:\/\//.test(value) || value.startsWith("data:image/");
}
