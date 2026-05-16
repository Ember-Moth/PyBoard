"use client";

import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { useRouter } from "next/navigation";
import type { ChangeEvent, FormEvent, ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

import CustomTextField from "@/app/(DashboardLayout)/components/forms/theme-elements/CustomTextField";
import TurnstileWidget from "@/components/auth/TurnstileWidget";
import { setAuthToken } from "@/lib/auth";
import { getGuestConfig, register, sendEmailVerify } from "@/services/auth.service";
import type { GuestConfig } from "@/types/api";

interface RegisterType {
  title?: string;
  subtitle?: ReactNode;
  subtext?: ReactNode;
}

const AuthRegister = ({ title, subtitle, subtext }: RegisterType) => {
  const router = useRouter();
  const [config, setConfig] = useState<GuestConfig | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const [turnstileKey, setTurnstileKey] = useState(0);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);

  useEffect(() => {
    getGuestConfig()
      .then(setConfig)
      .catch(() => setConfig({}));
  }, []);

  const handleVerify = useCallback((token: string) => {
    setTurnstileToken(token);
  }, []);

  const resetTurnstile = () => {
    setTurnstileToken("");
    setTurnstileKey((value) => value + 1);
  };

  const sendEmailCode = async () => {
    setError("");
    setMessage("");
    setSendingCode(true);
    try {
      await sendEmailVerify({
        email,
        recaptchaData: turnstileToken || undefined,
      });
      setMessage("验证码已发送，请检查邮箱。");
      resetTurnstile();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送验证码失败");
    } finally {
      setSendingCode(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const token = await register({
        email,
        password,
        inviteCode: inviteCode || undefined,
        emailCode: emailCode || undefined,
        recaptchaData: turnstileToken || undefined,
      });
      setAuthToken(token.auth_token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
      resetTurnstile();
    } finally {
      setLoading(false);
    }
  };

  const turnstileEnabled = Boolean(config?.is_recaptcha);
  const emailVerifyEnabled = Boolean(config?.is_email_verify);
  const inviteRequired = Boolean(config?.is_invite_force);

  return (
    <>
      {title ? (
        <Typography fontWeight="700" variant="h2" mb={1}>
          {title}
        </Typography>
      ) : null}

      {subtext}
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}
      {message ? (
        <Alert severity="success" sx={{ mb: 2 }}>
          {message}
        </Alert>
      ) : null}

      <Box component="form" onSubmit={handleSubmit}>
        <Stack mb={3}>
          <Typography variant="subtitle1" fontWeight={600} component="label" htmlFor="email" mb="5px">
            邮箱
          </Typography>
          <CustomTextField
            id="email"
            value={email}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setEmail(event.target.value)}
            variant="outlined"
            fullWidth
            required
          />

          <Typography variant="subtitle1" fontWeight={600} component="label" htmlFor="password" mb="5px" mt="25px">
            密码
          </Typography>
          <CustomTextField
            id="password"
            type="password"
            value={password}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setPassword(event.target.value)}
            variant="outlined"
            fullWidth
            required
          />

          {inviteRequired ? (
            <>
              <Typography
                variant="subtitle1"
                fontWeight={600}
                component="label"
                htmlFor="invite_code"
                mb="5px"
                mt="25px"
              >
                邀请码
              </Typography>
              <CustomTextField
                id="invite_code"
                value={inviteCode}
                onChange={(event: ChangeEvent<HTMLInputElement>) => setInviteCode(event.target.value)}
                variant="outlined"
                fullWidth
                required
              />
            </>
          ) : null}

          {emailVerifyEnabled ? (
            <>
              <Typography
                variant="subtitle1"
                fontWeight={600}
                component="label"
                htmlFor="email_code"
                mb="5px"
                mt="25px"
              >
                邮箱验证码
              </Typography>
              <Stack direction="row" spacing={1}>
                <CustomTextField
                  id="email_code"
                  value={emailCode}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setEmailCode(event.target.value)}
                  variant="outlined"
                  fullWidth
                  required
                />
                <Button
                  variant="outlined"
                  onClick={() => void sendEmailCode()}
                  disabled={sendingCode || !email || (turnstileEnabled && !turnstileToken)}
                >
                  {sendingCode ? "发送中" : "发送"}
                </Button>
              </Stack>
            </>
          ) : null}

          {turnstileEnabled ? (
            <Box mt={2} key={turnstileKey}>
              <TurnstileWidget
                siteKey={config?.turnstile_site_key || config?.recaptcha_site_key}
                onVerify={handleVerify}
              />
            </Box>
          ) : null}
        </Stack>
        <Button
          color="primary"
          variant="contained"
          size="large"
          fullWidth
          type="submit"
          disabled={loading || (turnstileEnabled && !turnstileToken)}
        >
          {loading ? "注册中..." : "注册"}
        </Button>
      </Box>
      {subtitle}
    </>
  );
};

export default AuthRegister;
