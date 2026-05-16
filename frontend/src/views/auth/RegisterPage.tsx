"use client";
import { Box, Card, Grid, Stack, Typography } from "@mui/material";
import Link from "next/link";
import Logo from "@/components/brand/Logo";
import PageContainer from "@/components/layout/PageContainer";
import { useSiteConfig } from "@/contexts/SiteConfigContext";
import AuthRegister from "@/features/auth/AuthRegister";

const Register2 = () => {
  const { loading: configLoading, registrationClosed } = useSiteConfig();

  return (
    <PageContainer title="注册" description="注册用户中心">
      <Box
        sx={{
          position: "relative",
          "&:before": {
            content: '""',
            background: "radial-gradient(#d2f1df, #d3d7fa, #bad8f4)",
            backgroundSize: "400% 400%",
            animation: "gradient 15s ease infinite",
            position: "absolute",
            height: "100%",
            width: "100%",
            opacity: "0.3",
          },
        }}
      >
        <Grid container spacing={0} justifyContent="center" sx={{ height: "100vh" }}>
          <Grid
            display="flex"
            justifyContent="center"
            alignItems="center"
            size={{
              xs: 12,
              sm: 12,
              lg: 4,
              xl: 3,
            }}
          >
            <Card elevation={9} sx={{ p: 4, zIndex: 1, width: "100%", maxWidth: "500px" }}>
              <Box display="flex" alignItems="center" justifyContent="center">
                <Logo />
              </Box>
              <AuthRegister
                subtext={
                  <Typography variant="subtitle1" textAlign="center" color="textSecondary" mb={1}>
                    {configLoading
                      ? "正在读取站点配置"
                      : registrationClosed
                        ? "当前暂不接受新账户注册"
                        : "创建账户后即可购买套餐并使用订阅"}
                  </Typography>
                }
                subtitle={
                  <Stack direction="row" justifyContent="center" spacing={1} mt={3}>
                    <Typography color="textSecondary" variant="h6" fontWeight="400">
                      已有账户？
                    </Typography>
                    <Typography
                      component={Link}
                      href="/auth/login"
                      fontWeight="500"
                      sx={{
                        textDecoration: "none",
                        color: "primary.main",
                      }}
                    >
                      去登录
                    </Typography>
                  </Stack>
                }
              />
            </Card>
          </Grid>
        </Grid>
      </Box>
    </PageContainer>
  );
};

export default Register2;
