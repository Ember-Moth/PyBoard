"use client";

import { Box, Container, styled } from "@mui/material";
import type { ReactNode } from "react";
import { useState } from "react";
import Header from "@/app/(DashboardLayout)/layout/header/Header";
import Sidebar from "@/app/(DashboardLayout)/layout/sidebar/Sidebar";
import AuthGuard from "@/components/auth/AuthGuard";

const MainWrapper = styled("div")(() => ({
  display: "flex",
  minHeight: "100vh",
  width: "100%",
}));

const PageWrapper = styled("div")(() => ({
  display: "flex",
  flexGrow: 1,
  paddingBottom: "60px",
  flexDirection: "column",
  zIndex: 1,
  backgroundColor: "transparent",
}));

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const [isSidebarOpen] = useState(true);
  const [isMobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <AuthGuard>
      <MainWrapper className="mainwrapper">
        <Sidebar
          isSidebarOpen={isSidebarOpen}
          isMobileSidebarOpen={isMobileSidebarOpen}
          onSidebarClose={() => setMobileSidebarOpen(false)}
        />
        <PageWrapper className="page-wrapper">
          <Header toggleMobileSidebar={() => setMobileSidebarOpen(true)} />
          <Container sx={{ paddingTop: "20px", maxWidth: "1200px" }}>
            <Box sx={{ minHeight: "calc(100vh - 170px)" }}>{children}</Box>
          </Container>
        </PageWrapper>
      </MainWrapper>
    </AuthGuard>
  );
}
