"use client";

import { Box, CircularProgress } from "@mui/material";
import { useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { clearAuthToken, getAuthToken } from "@/lib/auth";
import { getCurrentUser } from "@/services/auth.service";
import { ApiError } from "@/services/http";

type Props = {
  children: ReactNode;
};

export default function AuthGuard({ children }: Props) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.replace("/auth/login");
      return;
    }

    getCurrentUser()
      .then(() => setReady(true))
      .catch((error) => {
        if (error instanceof ApiError && error.status === 401) {
          clearAuthToken();
        }
        router.replace("/auth/login");
      });
  }, [router]);

  if (!ready) {
    return (
      <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center">
        <CircularProgress />
      </Box>
    );
  }

  return children;
}
