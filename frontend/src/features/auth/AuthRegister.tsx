"use client";

import { Alert, Box, Button, Checkbox, FormControlLabel, Stack, Typography } from "@mui/material";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import type { ChangeEvent, FormEvent, ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import TurnstileWidget from "@/components/auth/TurnstileWidget";
import CustomTextField from "@/components/forms/CustomTextField";
import { useSiteConfig } from "@/contexts/SiteConfigContext";
import { setAuthToken } from "@/lib/auth";
import { register, sendEmailVerify } from "@/services/auth.service";

interface RegisterType {
  title?: string;
  subtitle?: ReactNode;
  subtext?: ReactNode;
}

const AuthRegister = ({ title, subtitle, subtext }: RegisterType) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const {
    emailWhitelistSuffix,
    emailVerifyEnabled,
    inviteRequired,
    loading: configLoading,
    registrationClosed,
    tosUrl,
    turnstileEnabled,
    turnstileSiteKey,
  } = useSiteConfig();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState("");
  const [turnstileKey, setTurnstileKey] = useState(0);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);

  useEffect(() => {
    const code = searchParams.get("invite_code") || searchParams.get("code");
    if (code) {
      setInviteCode(code.toUpperCase());
    }
  }, [searchParams]);

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
    if (registrationClosed) {
      setError("当前停止注册");
      return;
    }
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
    if (registrationClosed) {
      setError("当前停止注册");
      return;
    }
    if (tosUrl && !acceptedTerms) {
      setError("请先阅读并同意服务条款");
      return;
    }
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
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
      resetTurnstile();
    } finally {
      setLoading(false);
    }
  };

  const formDisabled = configLoading || registrationClosed;

  return (
    <>
      {title ? (
        <Typography fontWeight="700" variant="h2" mb={1}>
          {title}
        </Typography>
      ) : null}

      {subtext}
      {registrationClosed ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          新用户注册暂未开放。
        </Alert>
      ) : null}
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
            disabled={formDisabled}
            helperText={
              emailWhitelistSuffix.length ? `允许注册的邮箱后缀：${emailWhitelistSuffix.join(", ")}` : undefined
            }
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
            disabled={formDisabled}
          />

          {inviteRequired || inviteCode ? (
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
                required={inviteRequired}
                disabled={formDisabled}
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
                  disabled={formDisabled}
                />
                <Button
                  variant="outlined"
                  onClick={() => void sendEmailCode()}
                  disabled={formDisabled || sendingCode || !email || (turnstileEnabled && !turnstileToken)}
                >
                  {sendingCode ? "发送中" : "发送"}
                </Button>
              </Stack>
            </>
          ) : null}

          {turnstileEnabled ? (
            <Box mt={2} key={turnstileKey}>
              <TurnstileWidget siteKey={turnstileSiteKey} onVerify={handleVerify} />
            </Box>
          ) : null}

          {tosUrl ? (
            <FormControlLabel
              sx={{ mt: 2, alignItems: "flex-start" }}
              control={
                <Checkbox
                  checked={acceptedTerms}
                  onChange={(event) => setAcceptedTerms(event.target.checked)}
                  disabled={formDisabled}
                />
              }
              label={
                <Typography variant="body2" color="text.secondary" pt={1}>
                  我已阅读并同意
                  <Typography
                    component={Link}
                    href={tosUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="body2"
                    sx={{ color: "primary.main", textDecoration: "none", ml: 0.5 }}
                  >
                    服务条款
                  </Typography>
                </Typography>
              }
            />
          ) : null}
        </Stack>
        <Button
          color="primary"
          variant="contained"
          size="large"
          fullWidth
          type="submit"
          disabled={
            formDisabled || loading || (turnstileEnabled && !turnstileToken) || Boolean(tosUrl && !acceptedTerms)
          }
        >
          {loading ? "注册中..." : "注册"}
        </Button>
      </Box>
      {subtitle}
    </>
  );
};

export default AuthRegister;
