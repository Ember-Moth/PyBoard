"use client";

import { Alert, Box, Button, Checkbox, FormControlLabel, FormGroup, Stack, Typography } from "@mui/material";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import type { ChangeEvent, FormEvent, ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";

import CustomTextField from "@/app/(DashboardLayout)/components/forms/theme-elements/CustomTextField";
import TurnstileWidget from "@/components/auth/TurnstileWidget";
import { setAuthToken } from "@/lib/auth";
import { getGuestConfig, login, quickLogin } from "@/services/auth.service";
import type { GuestConfig } from "@/types/api";

interface LoginType {
  title?: string;
  subtitle?: ReactNode;
  subtext?: ReactNode;
}

const AuthLogin = ({ title, subtitle, subtext }: LoginType) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [turnstileToken, setTurnstileToken] = useState("");
  const [config, setConfig] = useState<GuestConfig | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getGuestConfig()
      .then(setConfig)
      .catch(() => setConfig({}));
  }, []);

  useEffect(() => {
    const verify = searchParams.get("verify");
    if (!verify) {
      return;
    }
    quickLogin(verify)
      .then((data) => {
        if (data?.auth_token) {
          setAuthToken(data.auth_token);
          router.replace("/");
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "快捷登录失败"));
  }, [router, searchParams]);

  const handleVerify = useCallback((token: string) => {
    setTurnstileToken(token);
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const token = await login({
        email,
        password,
        recaptchaData: turnstileToken || undefined,
      });
      setAuthToken(token.auth_token, remember);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  };

  const turnstileEnabled = Boolean(config?.is_recaptcha);

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

      <Box component="form" onSubmit={handleSubmit}>
        <Stack>
          <Box>
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
          </Box>
          <Box mt="25px">
            <Typography variant="subtitle1" fontWeight={600} component="label" htmlFor="password" mb="5px">
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
          </Box>
          <Stack justifyContent="space-between" direction="row" alignItems="center" my={2}>
            <FormGroup>
              <FormControlLabel
                control={<Checkbox checked={remember} onChange={(event) => setRemember(event.target.checked)} />}
                label="保持登录"
              />
            </FormGroup>
            <Typography
              component={Link}
              href="/authentication/forgot"
              fontWeight="500"
              sx={{ textDecoration: "none", color: "primary.main" }}
            >
              忘记密码？
            </Typography>
          </Stack>
          {turnstileEnabled ? (
            <Box mb={2}>
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
          {loading ? "登录中..." : "登录"}
        </Button>
      </Box>
      {subtitle}
    </>
  );
};

export default AuthLogin;
