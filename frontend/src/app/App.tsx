"use client";

import { Box, Button, Stack, Typography } from "@mui/material";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ComponentType, useEffect } from "react";
import PageContainer from "@/components/layout/PageContainer";
import DashboardLayout from "@/layouts/dashboard/DashboardLayout";
import ForgotPasswordPage from "@/views/auth/ForgotPasswordPage";
import LoginPage from "@/views/auth/LoginPage";
import RegisterPage from "@/views/auth/RegisterPage";
import DashboardPage from "@/views/dashboard/DashboardPage";
import InvitePage from "@/views/invite/InvitePage";
import LandingPage from "@/views/landing/LandingPage";
import OrdersPage from "@/views/orders/OrdersPage";
import PlansPage from "@/views/plans/PlansPage";
import SettingsPage from "@/views/settings/SettingsPage";
import SubscribePage from "@/views/subscribe/SubscribePage";
import TicketsPage from "@/views/tickets/TicketsPage";

const AUTH_ROUTES: Record<string, ComponentType> = {
  "/auth/forgot": ForgotPasswordPage,
  "/auth/login": LoginPage,
  "/auth/register": RegisterPage,
};

const DASHBOARD_ROUTES: Record<string, ComponentType> = {
  "/dashboard": DashboardPage,
  "/invite": InvitePage,
  "/orders": OrdersPage,
  "/plans": PlansPage,
  "/settings": SettingsPage,
  "/subscribe": SubscribePage,
  "/tickets": TicketsPage,
};

export default function App() {
  const pathname = normalizePath(usePathname());
  const router = useRouter();

  useEffect(() => {
    const hash = window.location.hash;
    if (hash.startsWith("#/login?")) {
      router.replace(`/auth/login?${hash.slice("#/login?".length)}`);
    }
  }, [router]);

  const AuthPage = AUTH_ROUTES[pathname];
  if (AuthPage) {
    return <AuthPage />;
  }

  if (pathname === "/") {
    return <LandingPage />;
  }

  const DashboardRoute = DASHBOARD_ROUTES[pathname];
  return <DashboardLayout>{DashboardRoute ? <DashboardRoute /> : <SpaNotFound />}</DashboardLayout>;
}

function SpaNotFound() {
  return (
    <PageContainer title="页面不存在" description="当前页面不存在">
      <Box minHeight="60vh" display="flex" alignItems="center" justifyContent="center">
        <Stack spacing={2} textAlign="center" alignItems="center">
          <Typography variant="h3">页面不存在</Typography>
          <Typography color="text.secondary">请返回仪表盘，或从侧栏重新选择功能。</Typography>
          <Button component={Link} href="/dashboard" variant="contained">
            返回仪表盘
          </Button>
        </Stack>
      </Box>
    </PageContainer>
  );
}

function normalizePath(pathname: string | null): string {
  if (!pathname || pathname === "/") {
    return "/";
  }
  return pathname.replace(/\/+$/, "");
}
