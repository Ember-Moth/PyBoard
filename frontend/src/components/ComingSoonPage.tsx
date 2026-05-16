"use client";

import { Box, Card, CardContent, Typography } from "@mui/material";

import PageContainer from "@/app/(DashboardLayout)/components/container/PageContainer";

type Props = {
  title: string;
  description: string;
};

export default function ComingSoonPage({ title, description }: Props) {
  return (
    <PageContainer title={title} description={description}>
      <Card elevation={9}>
        <CardContent>
          <Box maxWidth={720}>
            <Typography variant="h3" mb={1}>
              {title}
            </Typography>
            <Typography color="text.secondary">{description}</Typography>
            <Typography color="text.secondary" mt={2}>
              第一阶段先完成用户仪表盘、登录注册和基础鉴权；该页面会在后续接入完整业务流。
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </PageContainer>
  );
}
