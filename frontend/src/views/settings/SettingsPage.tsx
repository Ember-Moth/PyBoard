"use client";

import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Skeleton,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import {
  IconBrandTelegram,
  IconCopy,
  IconDeviceFloppy,
  IconKey,
  IconLink,
  IconRefresh,
  IconShieldCheck,
} from "@tabler/icons-react";
import type { ChangeEvent, Dispatch, FormEvent, ReactNode, SetStateAction } from "react";
import { useEffect, useState } from "react";
import CustomTextField from "@/components/forms/CustomTextField";
import PageContainer from "@/components/layout/PageContainer";
import { useSiteConfig } from "@/contexts/SiteConfigContext";
import { formatDateTime, formatMoney } from "@/lib/format";
import {
  changeUserPassword,
  createQuickLoginUrl,
  getUserProfile,
  resetUserSecurity,
  unbindTelegram,
  updateUserProfile,
} from "@/services/user.service";
import type { UserProfile } from "@/types/api";

type PreferenceState = {
  autoRenewal: boolean;
  remindExpire: boolean;
  remindTraffic: boolean;
};

type PasswordState = {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
};

const EMPTY_PASSWORD: PasswordState = {
  oldPassword: "",
  newPassword: "",
  confirmPassword: "",
};

export default function SettingsPage() {
  const { currencySymbol } = useSiteConfig();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [preferences, setPreferences] = useState<PreferenceState>({
    autoRenewal: false,
    remindExpire: false,
    remindTraffic: false,
  });
  const [password, setPassword] = useState<PasswordState>(EMPTY_PASSWORD);
  const [quickLoginUrl, setQuickLoginUrl] = useState("");
  const [copied, setCopied] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [resettingSecurity, setResettingSecurity] = useState(false);
  const [generatingQuickLogin, setGeneratingQuickLogin] = useState(false);
  const [unbindingTelegram, setUnbindingTelegram] = useState(false);

  const loadProfile = async () => {
    setError("");
    setLoading(true);
    try {
      const nextProfile = await getUserProfile();
      setProfile(nextProfile);
      setPreferences({
        autoRenewal: Boolean(nextProfile.auto_renewal),
        remindExpire: Boolean(nextProfile.remind_expire),
        remindTraffic: Boolean(nextProfile.remind_traffic),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "账户设置加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    getUserProfile()
      .then((nextProfile) => {
        if (cancelled) {
          return;
        }
        setProfile(nextProfile);
        setPreferences({
          autoRenewal: Boolean(nextProfile.auto_renewal),
          remindExpire: Boolean(nextProfile.remind_expire),
          remindTraffic: Boolean(nextProfile.remind_traffic),
        });
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "账户设置加载失败");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const savePreferences = async () => {
    setError("");
    setSuccess("");
    setSavingPreferences(true);
    try {
      await updateUserProfile({
        auto_renewal: preferences.autoRenewal ? 1 : 0,
        remind_expire: preferences.remindExpire ? 1 : 0,
        remind_traffic: preferences.remindTraffic ? 1 : 0,
      });
      setSuccess("账户偏好已保存");
      await loadProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存账户偏好失败");
    } finally {
      setSavingPreferences(false);
    }
  };

  const submitPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (password.newPassword !== password.confirmPassword) {
      setError("两次输入的新密码不一致");
      return;
    }
    setChangingPassword(true);
    try {
      await changeUserPassword({
        oldPassword: password.oldPassword,
        newPassword: password.newPassword,
      });
      setPassword(EMPTY_PASSWORD);
      setSuccess("密码已更新");
    } catch (err) {
      setError(err instanceof Error ? err.message : "修改密码失败");
    } finally {
      setChangingPassword(false);
    }
  };

  const resetSecurity = async () => {
    setError("");
    setSuccess("");
    setResettingSecurity(true);
    try {
      const result = await resetUserSecurity();
      setProfile((current) => (current ? { ...current, uuid: result.uuid } : current));
      setSuccess("订阅安全标识已重置");
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置安全标识失败");
    } finally {
      setResettingSecurity(false);
    }
  };

  const generateQuickLoginUrl = async () => {
    setError("");
    setSuccess("");
    setGeneratingQuickLogin(true);
    try {
      const url = await createQuickLoginUrl();
      setQuickLoginUrl(url);
      setSuccess("快捷登录链接已生成，60 秒内有效");
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成快捷登录链接失败");
    } finally {
      setGeneratingQuickLogin(false);
    }
  };

  const unbindTelegramAccount = async () => {
    setError("");
    setSuccess("");
    setUnbindingTelegram(true);
    try {
      await unbindTelegram();
      setProfile((current) => (current ? { ...current, telegram_id: null } : current));
      setSuccess("Telegram 已解绑");
    } catch (err) {
      setError(err instanceof Error ? err.message : "解绑 Telegram 失败");
    } finally {
      setUnbindingTelegram(false);
    }
  };

  const copyText = async (key: string, value: string) => {
    await navigator.clipboard.writeText(value);
    setCopied(key);
    window.setTimeout(() => setCopied(""), 1800);
  };

  if (loading && !profile) {
    return <SettingsSkeleton />;
  }

  return (
    <PageContainer title="账户设置" description="修改账户偏好、密码和订阅安全标识">
      <Stack spacing={3}>
        <Box>
          <Typography variant="h3">账户设置</Typography>
          <Typography variant="body1" color="text.secondary" mt={0.5}>
            管理账户偏好、密码和订阅安全信息。
          </Typography>
        </Box>

        {error ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={() => void loadProfile()}>
                重试
              </Button>
            }
          >
            {error}
          </Alert>
        ) : null}
        {success ? <Alert severity="success">{success}</Alert> : null}

        {profile ? (
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, lg: 5 }}>
              <AccountCard profile={profile} currencySymbol={currencySymbol} />
            </Grid>

            <Grid size={{ xs: 12, lg: 7 }}>
              <Card elevation={9}>
                <CardContent>
                  <Stack spacing={3}>
                    <SectionHeader
                      icon={<IconDeviceFloppy size={20} />}
                      title="账户偏好"
                      description="这些偏好会影响续费和账户提醒行为。"
                    />
                    <PreferenceSwitch
                      title="自动续费"
                      description="套餐到期前自动创建续费流程。"
                      checked={preferences.autoRenewal}
                      onChange={(value) => setPreferences((current) => ({ ...current, autoRenewal: value }))}
                    />
                    <PreferenceSwitch
                      title="到期提醒"
                      description="套餐临近到期时显示提醒。"
                      checked={preferences.remindExpire}
                      onChange={(value) => setPreferences((current) => ({ ...current, remindExpire: value }))}
                    />
                    <PreferenceSwitch
                      title="流量提醒"
                      description="流量接近用尽时显示提醒。"
                      checked={preferences.remindTraffic}
                      onChange={(value) => setPreferences((current) => ({ ...current, remindTraffic: value }))}
                    />
                    <Box>
                      <Button
                        variant="contained"
                        startIcon={<IconDeviceFloppy size={18} />}
                        onClick={() => void savePreferences()}
                        disabled={savingPreferences}
                      >
                        {savingPreferences ? "保存中..." : "保存偏好"}
                      </Button>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, lg: 6 }}>
              <Card elevation={9}>
                <CardContent>
                  <Stack spacing={3}>
                    <SectionHeader icon={<IconKey size={20} />} title="修改密码" description="新密码至少 8 位。" />
                    <Box component="form" onSubmit={submitPassword}>
                      <Stack spacing={2}>
                        <CustomTextField
                          label="当前密码"
                          type="password"
                          value={password.oldPassword}
                          onChange={handlePasswordChange("oldPassword", setPassword)}
                          required
                          fullWidth
                        />
                        <CustomTextField
                          label="新密码"
                          type="password"
                          value={password.newPassword}
                          onChange={handlePasswordChange("newPassword", setPassword)}
                          required
                          fullWidth
                        />
                        <CustomTextField
                          label="确认新密码"
                          type="password"
                          value={password.confirmPassword}
                          onChange={handlePasswordChange("confirmPassword", setPassword)}
                          required
                          fullWidth
                        />
                        <Button
                          type="submit"
                          variant="contained"
                          startIcon={<IconKey size={18} />}
                          disabled={changingPassword}
                        >
                          {changingPassword ? "提交中..." : "修改密码"}
                        </Button>
                      </Stack>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, lg: 6 }}>
              <Card elevation={9}>
                <CardContent>
                  <Stack spacing={3}>
                    <SectionHeader
                      icon={<IconShieldCheck size={20} />}
                      title="安全标识"
                      description="重置后旧订阅链接会失效，需要重新导入订阅。"
                    />
                    <ReadonlyValue
                      label="订阅 UUID"
                      value={profile.uuid}
                      action={
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<IconCopy size={16} />}
                          onClick={() => void copyText("uuid", profile.uuid)}
                        >
                          {copied === "uuid" ? "已复制" : "复制"}
                        </Button>
                      }
                    />
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<IconRefresh size={18} />}
                      onClick={() => void resetSecurity()}
                      disabled={resettingSecurity}
                    >
                      {resettingSecurity ? "重置中..." : "重置订阅安全标识"}
                    </Button>
                    <Divider />
                    <SectionHeader
                      icon={<IconLink size={20} />}
                      title="快捷登录"
                      description="生成的一次性链接 60 秒内有效。"
                    />
                    {quickLoginUrl ? (
                      <ReadonlyValue
                        label="快捷登录链接"
                        value={quickLoginUrl}
                        action={
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<IconCopy size={16} />}
                            onClick={() => void copyText("quick-login", quickLoginUrl)}
                          >
                            {copied === "quick-login" ? "已复制" : "复制"}
                          </Button>
                        }
                      />
                    ) : null}
                    <Button
                      variant="contained"
                      startIcon={<IconLink size={18} />}
                      onClick={() => void generateQuickLoginUrl()}
                      disabled={generatingQuickLogin}
                    >
                      {generatingQuickLogin ? "生成中..." : "生成快捷登录链接"}
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Card elevation={9}>
                <CardContent>
                  <Stack
                    direction={{ xs: "column", md: "row" }}
                    spacing={2}
                    justifyContent="space-between"
                    alignItems={{ xs: "flex-start", md: "center" }}
                  >
                    <SectionHeader
                      icon={<IconBrandTelegram size={20} />}
                      title="Telegram"
                      description={
                        profile.telegram_id
                          ? `已绑定 Telegram ID：${profile.telegram_id}`
                          : "当前账户尚未绑定 Telegram。"
                      }
                    />
                    <Button
                      variant="outlined"
                      color="secondary"
                      startIcon={<IconBrandTelegram size={18} />}
                      onClick={() => void unbindTelegramAccount()}
                      disabled={!profile.telegram_id || unbindingTelegram}
                    >
                      {unbindingTelegram ? "解绑中..." : "解绑 Telegram"}
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : null}
      </Stack>
    </PageContainer>
  );
}

function AccountCard({ profile, currencySymbol }: { profile: UserProfile; currencySymbol: string }) {
  return (
    <Card elevation={9}>
      <CardContent>
        <Stack spacing={3}>
          <Stack direction="row" spacing={2} alignItems="center">
            <Avatar src={profile.avatar_url} alt={profile.email} sx={{ width: 64, height: 64 }} />
            <Box minWidth={0}>
              <Typography variant="h5" noWrap>
                {profile.email}
              </Typography>
              <Stack direction="row" spacing={1} mt={1} flexWrap="wrap" useFlexGap>
                <Chip
                  size="small"
                  color={profile.banned ? "error" : "success"}
                  label={profile.banned ? "已封禁" : "正常"}
                />
                {profile.plan_id ? <Chip size="small" variant="outlined" label={`套餐 #${profile.plan_id}`} /> : null}
              </Stack>
            </Box>
          </Stack>
          <Divider />
          <Stack spacing={1.5}>
            <InfoRow label="账户余额" value={formatMoney(profile.balance, currencySymbol)} />
            <InfoRow label="佣金余额" value={formatMoney(profile.commission_balance, currencySymbol)} />
            <InfoRow label="到期时间" value={formatDateTime(profile.expired_at)} />
            <InfoRow label="注册时间" value={formatDateTime(profile.created_at)} />
            <InfoRow label="上次登录" value={formatDateTime(profile.last_login_at)} />
          </Stack>
        </Stack>
      </CardContent>
    </Card>
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

function PreferenceSwitch({
  title,
  description,
  checked,
  onChange,
}: {
  title: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <Stack direction="row" justifyContent="space-between" spacing={2} alignItems="center">
      <Box>
        <Typography fontWeight={600}>{title}</Typography>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Box>
      <Switch checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </Stack>
  );
}

function ReadonlyValue({ label, value, action }: { label: string; value: string; action?: ReactNode }) {
  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
        p: 1.5,
      }}
    >
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between" mt={0.5}>
        <Typography variant="body2" sx={{ wordBreak: "break-all" }}>
          {value}
        </Typography>
        {action}
      </Stack>
    </Box>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <Stack direction="row" justifyContent="space-between" spacing={2}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" fontWeight={600} textAlign="right">
        {value}
      </Typography>
    </Stack>
  );
}

function SettingsSkeleton() {
  return (
    <PageContainer title="账户设置" description="修改账户偏好、密码和订阅安全标识">
      <Stack spacing={3}>
        <Box>
          <Skeleton width={160} height={42} />
          <Skeleton width={280} />
        </Box>
        <Grid container spacing={3}>
          {[0, 1, 2, 3].map((item) => (
            <Grid size={{ xs: 12, md: 6 }} key={item}>
              <Card elevation={9}>
                <CardContent>
                  <Skeleton height={32} width="45%" />
                  <Skeleton height={120} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Stack>
    </PageContainer>
  );
}

function handlePasswordChange(field: keyof PasswordState, setPassword: Dispatch<SetStateAction<PasswordState>>) {
  return (event: ChangeEvent<HTMLInputElement>) => {
    setPassword((current) => ({ ...current, [field]: event.target.value }));
  };
}
