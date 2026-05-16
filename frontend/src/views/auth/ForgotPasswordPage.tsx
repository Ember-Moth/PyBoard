"use client";

import { Alert, Box, Button, Card, Grid, Stack, Typography } from "@mui/material";
import Link from "next/link";
import { useCallback, useState } from "react";
import TurnstileWidget from "@/components/auth/TurnstileWidget";
import Logo from "@/components/brand/Logo";
import CustomTextField from "@/components/forms/CustomTextField";
import PageContainer from "@/components/layout/PageContainer";
import { useSiteConfig } from "@/contexts/SiteConfigContext";
import { forgetPassword, sendEmailVerify } from "@/services/auth.service";

export default function ForgotPasswordPage() {
  const { turnstileEnabled, turnstileSiteKey } = useSiteConfig();
  const [email, setEmail] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [password, setPassword] = useState("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const [turnstileKey, setTurnstileKey] = useState(0);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);

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
        isForget: true,
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

  const resetPassword = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      await forgetPassword({
        email,
        emailCode,
        password,
        recaptchaData: turnstileToken || undefined,
      });
      setMessage("密码已重置，可以返回登录。");
      resetTurnstile();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置密码失败");
      resetTurnstile();
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer title="忘记密码" description="重置用户密码">
      <Box sx={{ position: "relative", minHeight: "100vh", backgroundColor: "grey.100" }}>
        <Grid container justifyContent="center" sx={{ minHeight: "100vh" }}>
          <Grid display="flex" justifyContent="center" alignItems="center" size={{ xs: 12, sm: 10, md: 6, lg: 4 }}>
            <Card elevation={9} sx={{ p: 4, width: "100%", maxWidth: 500 }}>
              <Box display="flex" alignItems="center" justifyContent="center" mb={2}>
                <Logo />
              </Box>
              <Typography variant="h4" mb={1}>
                重置密码
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={2}>
                通过邮箱验证码设置新的登录密码。
              </Typography>
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
              <Box component="form" onSubmit={resetPassword}>
                <Stack spacing={2}>
                  <CustomTextField
                    label="邮箱"
                    value={email}
                    onChange={(event: React.ChangeEvent<HTMLInputElement>) => setEmail(event.target.value)}
                    required
                    fullWidth
                  />
                  <Stack direction="row" spacing={1}>
                    <CustomTextField
                      label="邮箱验证码"
                      value={emailCode}
                      onChange={(event: React.ChangeEvent<HTMLInputElement>) => setEmailCode(event.target.value)}
                      required
                      fullWidth
                    />
                    <Button
                      variant="outlined"
                      onClick={() => void sendEmailCode()}
                      disabled={sendingCode || !email || (turnstileEnabled && !turnstileToken)}
                    >
                      {sendingCode ? "发送中" : "发送"}
                    </Button>
                  </Stack>
                  <CustomTextField
                    label="新密码"
                    type="password"
                    value={password}
                    onChange={(event: React.ChangeEvent<HTMLInputElement>) => setPassword(event.target.value)}
                    required
                    fullWidth
                  />
                  {turnstileEnabled ? (
                    <Box key={turnstileKey}>
                      <TurnstileWidget siteKey={turnstileSiteKey} onVerify={handleVerify} />
                    </Box>
                  ) : null}
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    disabled={loading || (turnstileEnabled && !turnstileToken)}
                  >
                    {loading ? "提交中..." : "重置密码"}
                  </Button>
                </Stack>
              </Box>
              <Typography
                component={Link}
                href="/auth/login"
                display="block"
                textAlign="center"
                mt={3}
                sx={{ textDecoration: "none", color: "primary.main" }}
              >
                返回登录
              </Typography>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </PageContainer>
  );
}
