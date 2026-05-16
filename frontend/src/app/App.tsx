"use client";

import { Box, Button, CircularProgress, Stack, Typography } from "@mui/material";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { type ComponentType, useEffect } from "react";
import PageContainer from "@/components/layout/PageContainer";
import DashboardLayout from "@/layouts/dashboard/DashboardLayout";
import { useSpaPathname } from "@/lib/spa-navigation";
import LandingPage from "@/views/landing/LandingPage";

const ForgotPasswordPage = dynamic(() => import("@/views/auth/ForgotPasswordPage"), { loading: RouteLoading });
const LoginPage = dynamic(() => import("@/views/auth/LoginPage"), { loading: RouteLoading });
const RegisterPage = dynamic(() => import("@/views/auth/RegisterPage"), { loading: RouteLoading });
const DashboardPage = dynamic(() => import("@/views/dashboard/DashboardPage"), { loading: RouteLoading });
const InvitePage = dynamic(() => import("@/views/invite/InvitePage"), { loading: RouteLoading });
const OrdersPage = dynamic(() => import("@/views/orders/OrdersPage"), { loading: RouteLoading });
const PlansPage = dynamic(() => import("@/views/plans/PlansPage"), { loading: RouteLoading });
const SettingsPage = dynamic(() => import("@/views/settings/SettingsPage"), { loading: RouteLoading });
const SubscribePage = dynamic(() => import("@/views/subscribe/SubscribePage"), { loading: RouteLoading });
const TicketsPage = dynamic(() => import("@/views/tickets/TicketsPage"), { loading: RouteLoading });

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
  const pathname = useSpaPathname();
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

function RouteLoading() {
  return (
    <Box minHeight="50vh" display="flex" alignItems="center" justifyContent="center">
      <CircularProgress size={28} />
    </Box>
  );
}
