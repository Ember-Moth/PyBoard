"use client";

import { Box, Button, Chip, Container, Divider, Grid, Stack, Typography } from "@mui/material";
import {
  IconBolt,
  IconBrandTelegram,
  IconCheck,
  IconCreditCard,
  IconGauge,
  IconHeadset,
  IconKey,
  IconLogin2,
  IconReceipt2,
  IconRocket,
  IconServer,
  IconShieldCheck,
  IconShieldLock,
  IconUserPlus,
  IconWifi,
} from "@tabler/icons-react";
import Link from "next/link";
import type { ReactNode } from "react";

import PageContainer from "@/components/layout/PageContainer";
import { useSiteConfig } from "@/contexts/SiteConfigContext";
import { getAuthToken } from "@/lib/auth";
import type { FooterConfig, FooterItemConfig } from "@/types/config";

const CAPABILITIES = [
  {
    icon: <IconServer size={22} />,
    title: "多地区代理节点",
    text: "按套餐提供可用线路，用户可以在节点列表中查看协议、地址、端口和倍率信息。",
  },
  {
    icon: <IconWifi size={22} />,
    title: "主流客户端订阅",
    text: "购买后复制订阅链接，导入到常见代理客户端，减少手动配置节点的成本。",
  },
  {
    icon: <IconGauge size={22} />,
    title: "流量和设备透明",
    text: "套餐流量、到期时间、在线设备和节点使用记录集中展示，用户知道自己买到了什么。",
  },
  {
    icon: <IconCreditCard size={22} />,
    title: "购买续费清晰",
    text: "套餐、订单、支付状态和续费路径放在同一套流程里，降低用户从选购到使用的断点。",
  },
];

const STEPS = [
  {
    title: "注册或登录账户",
    text: "创建账户后进入账户中心，站点关闭注册时已有用户仍可直接登录。",
  },
  {
    title: "选择节点套餐",
    text: "按流量、周期、设备数和线路需求选择合适的 VPN 代理节点套餐。",
  },
  {
    title: "导入订阅使用",
    text: "复制订阅链接到常用客户端，查看节点列表，并按需续费或重置订阅。",
  },
];

const PREVIEW_ROWS = [
  { label: "节点地区", value: "多地区", color: "#5D87FF" },
  { label: "设备支持", value: "多端", color: "#13DEB9" },
  { label: "套餐流量", value: "清晰可查", color: "#FFAE1F" },
];

const DEFAULT_PANEL_DESCRIPTION = "PyBoard panel backend.";
const DEFAULT_SERVICE_DESCRIPTION = "提供稳定的 VPN 代理节点服务，支持套餐购买、订阅导入、流量查看和工单支持。";

export default function LandingPage() {
  const { appDescription, appName, appUrl, config, footer, logo, registrationClosed, tosUrl } = useSiteConfig();
  const authed = Boolean(getAuthToken());
  const primaryHref = authed ? "/dashboard" : "/auth/login";
  const primaryLabel = authed ? "我的套餐" : "登录购买";
  const telegramLink = config.telegram_discuss_link?.trim();
  const landingDescription = getLandingDescription(appDescription);
  const seoKeywords = getSeoKeywords(footer, appName);

  return (
    <PageContainer title="首页" description={landingDescription} keywords={seoKeywords}>
      <Box bgcolor="#f6f8fb" minHeight="100vh">
        <LandingHeader
          appName={appName}
          authed={authed}
          logo={logo}
          primaryHref={primaryHref}
          primaryLabel={primaryLabel}
          registrationClosed={registrationClosed}
        />

        <HeroSection appDescription={landingDescription} appName={appName} />

        <Box component="main">
          <ProductSection />
          <CapabilitiesSection />
          <WorkflowSection registrationClosed={registrationClosed} />
          <TrustSection telegramLink={telegramLink} />
          <SiteFooter
            appDescription={landingDescription}
            appName={appName}
            appUrl={appUrl}
            footer={footer}
            telegramLink={telegramLink}
            tosUrl={tosUrl}
          />
        </Box>
      </Box>
    </PageContainer>
  );
}

function LandingHeader({
  appName,
  authed,
  logo,
  primaryHref,
  primaryLabel,
  registrationClosed,
}: {
  appName: string;
  authed: boolean;
  logo: string;
  primaryHref: string;
  primaryLabel: string;
  registrationClosed: boolean;
}) {
  return (
    <Box
      component="header"
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 20,
        borderBottom: "1px solid rgba(42, 53, 71, 0.1)",
        bgcolor: "rgba(255,255,255,0.9)",
        backdropFilter: "blur(16px)",
      }}
    >
      <Container maxWidth="lg">
        <Stack direction="row" alignItems="center" justifyContent="space-between" minHeight={72} spacing={2}>
          <Stack direction="row" alignItems="center" spacing={1.5} minWidth={0} sx={{ flex: "1 1 auto" }}>
            {logo ? (
              <Box
                component="img"
                src={logo}
                alt={appName}
                sx={{ maxHeight: 38, maxWidth: 154, objectFit: "contain" }}
              />
            ) : (
              <Box
                sx={{
                  width: 38,
                  height: 38,
                  borderRadius: 1,
                  display: "grid",
                  placeItems: "center",
                  color: "#fff",
                  bgcolor: "#2A3547",
                }}
              >
                <IconRocket size={22} />
              </Box>
            )}
            <Typography variant="h5" noWrap>
              {appName}
            </Typography>
          </Stack>

          <Stack
            component="nav"
            direction="row"
            spacing={0.5}
            sx={{ display: { xs: "none", md: "flex" } }}
            aria-label="首页导航"
          >
            <Button component="a" href="#product" color="inherit">
              节点
            </Button>
            <Button component="a" href="#capabilities" color="inherit">
              套餐
            </Button>
            <Button component="a" href="#workflow" color="inherit">
              使用
            </Button>
          </Stack>

          <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
            <Button component={Link} href={primaryHref} variant="outlined" startIcon={<IconLogin2 size={18} />}>
              {primaryLabel}
            </Button>
            {!authed && !registrationClosed ? (
              <Button
                component={Link}
                href="/auth/register"
                variant="contained"
                startIcon={<IconUserPlus size={18} />}
                sx={{ display: { xs: "none", sm: "inline-flex" } }}
              >
                注册选购
              </Button>
            ) : null}
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}

function HeroSection({ appDescription, appName }: { appDescription: string; appName: string }) {
  return (
    <Box
      component="section"
      sx={{
        position: "relative",
        overflow: "hidden",
        minHeight: { xs: "72svh", md: "74svh" },
        display: "flex",
        alignItems: "center",
        color: "#fff",
        bgcolor: "#112032",
        backgroundImage:
          "linear-gradient(90deg, rgba(17,32,50,0.98) 0%, rgba(17,32,50,0.88) 45%, rgba(17,32,50,0.58) 100%), url('/images/backgrounds/rocket.png')",
        backgroundRepeat: "no-repeat",
        backgroundPosition: {
          xs: "right -28px bottom 24px",
          md: "right 10% center",
        },
        backgroundSize: {
          xs: "190px auto",
          sm: "250px auto",
          md: "360px auto",
        },
      }}
    >
      <Box
        aria-hidden="true"
        sx={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
          maskImage: "linear-gradient(90deg, rgba(0,0,0,0.7), transparent 82%)",
        }}
      />
      <Container maxWidth="lg" sx={{ position: "relative" }}>
        <Stack spacing={3} maxWidth={700} py={{ xs: 7, md: 9 }}>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip label="VPN 代理节点" sx={{ bgcolor: "#FFAE1F", color: "#111827", fontWeight: 700 }} />
            <Chip label="多地区线路" sx={{ bgcolor: "rgba(255,255,255,0.14)", color: "#fff" }} />
            <Chip label="一键订阅导入" sx={{ bgcolor: "rgba(19,222,185,0.18)", color: "#D8FFF7" }} />
          </Stack>

          <Box>
            <Typography
              component="h1"
              sx={{
                fontSize: { xs: 40, sm: 52, md: 68 },
                fontWeight: 800,
                lineHeight: 1.04,
                letterSpacing: 0,
                maxWidth: 620,
              }}
            >
              {appName}
            </Typography>
            <Typography variant="h5" color="rgba(255,255,255,0.78)" mt={2.5} maxWidth={640}>
              {appDescription}
            </Typography>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}

function ProductSection() {
  return (
    <Box component="section" id="product" py={{ xs: 6, md: 9 }}>
      <Container maxWidth="lg">
        <Grid container spacing={{ xs: 3, md: 5 }} alignItems="center">
          <Grid size={{ xs: 12, md: 5 }}>
            <SectionEyebrow icon={<IconServer size={18} />} label="节点服务" />
            <Typography
              component="h2"
              sx={{
                fontSize: { xs: 30, md: 42 },
                fontWeight: 800,
                lineHeight: 1.15,
                mt: 1.5,
              }}
            >
              把线路、套餐和订阅体验放在第一位
            </Typography>
            <Typography variant="body1" color="text.secondary" mt={2}>
              核心体验围绕节点套餐展开：清晰的流量和周期，明确的订阅导入方式，以及出现连接或订单问题时可追踪的支持流程。
            </Typography>
            <Stack spacing={1.25} mt={3}>
              <CheckLine>套餐流量、周期、设备数和到期时间清楚展示</CheckLine>
              <CheckLine>购买后复制订阅链接，导入到常用代理客户端</CheckLine>
              <CheckLine>节点列表、流量记录和工单支持集中在账户中心</CheckLine>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, md: 7 }}>
            <ServicePreview />
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

function ServicePreview() {
  return (
    <Box
      sx={{
        border: "1px solid rgba(42,53,71,0.12)",
        borderRadius: 2,
        bgcolor: "#fff",
        boxShadow: "0 24px 70px rgba(42,53,71,0.12)",
        overflow: "hidden",
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ px: { xs: 2, md: 3 }, py: 2, bgcolor: "#F8FAFC" }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <Box
            sx={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              bgcolor: "#FA896B",
            }}
          />
          <Box
            sx={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              bgcolor: "#FFAE1F",
            }}
          />
          <Box
            sx={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              bgcolor: "#13DEB9",
            }}
          />
        </Stack>
        <Chip size="small" label="账户正常" color="success" />
      </Stack>

      <Box sx={{ p: { xs: 2.5, md: 3 } }}>
        <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              节点套餐
            </Typography>
            <Typography variant="h4" mt={0.5}>
              标准代理套餐
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <PreviewAction icon={<IconKey size={16} />} label="订阅导入" />
            <PreviewAction icon={<IconServer size={16} />} label="查看节点" />
          </Stack>
        </Stack>

        <Box mt={3}>
          <Stack direction="row" justifyContent="space-between" mb={1}>
            <Typography variant="subtitle2">套餐流量</Typography>
            <Typography variant="subtitle2" color="text.secondary">
              34%
            </Typography>
          </Stack>
          <Box
            sx={{
              height: 10,
              borderRadius: 5,
              bgcolor: "#EAEFF4",
              overflow: "hidden",
            }}
          >
            <Box sx={{ width: "34%", height: "100%", bgcolor: "#5D87FF" }} />
          </Box>
        </Box>

        <Grid container spacing={2} mt={1}>
          {PREVIEW_ROWS.map((item) => (
            <Grid size={{ xs: 12, sm: 4 }} key={item.label}>
              <Box
                sx={{
                  p: 2,
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: 1,
                  height: "100%",
                }}
              >
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      bgcolor: item.color,
                    }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {item.label}
                  </Typography>
                </Stack>
                <Typography variant="h5" mt={1}>
                  {item.value}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>

        <Divider sx={{ my: 2.5 }} />

        <Grid container spacing={2}>
          <PreviewSummary icon={<IconReceipt2 size={18} />} label="订单状态" value="已开通" />
          <PreviewSummary icon={<IconHeadset size={18} />} label="售后支持" value="工单" />
          <PreviewSummary icon={<IconBolt size={18} />} label="连接方式" value="订阅" />
        </Grid>
      </Box>
    </Box>
  );
}

function CapabilitiesSection() {
  return (
    <Box component="section" id="capabilities" sx={{ py: { xs: 6, md: 9 }, bgcolor: "#fff" }}>
      <Container maxWidth="lg">
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={3} mb={{ xs: 3, md: 4 }}>
          <Box maxWidth={620}>
            <SectionEyebrow icon={<IconShieldCheck size={18} />} label="服务能力" />
            <Typography
              component="h2"
              sx={{
                fontSize: { xs: 30, md: 42 },
                fontWeight: 800,
                lineHeight: 1.15,
                mt: 1.5,
              }}
            >
              围绕 VPN 代理节点的购买和使用设计
            </Typography>
          </Box>
        </Stack>

        <Grid container spacing={2.5}>
          {CAPABILITIES.map((item) => (
            <Grid size={{ xs: 12, md: 6 }} key={item.title}>
              <Box
                sx={{
                  bgcolor: "#F8FAFC",
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: 1,
                  p: { xs: 2.5, md: 3 },
                  height: "100%",
                }}
              >
                <Stack direction="row" spacing={2} alignItems="flex-start">
                  <Box
                    sx={{
                      width: 44,
                      height: 44,
                      borderRadius: 1,
                      display: "grid",
                      placeItems: "center",
                      color: "#fff",
                      bgcolor: "#2A3547",
                      flex: "0 0 auto",
                    }}
                  >
                    {item.icon}
                  </Box>
                  <Box minWidth={0}>
                    <Typography variant="h5">{item.title}</Typography>
                    <Typography variant="body2" color="text.secondary" mt={0.75}>
                      {item.text}
                    </Typography>
                  </Box>
                </Stack>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}

function WorkflowSection({ registrationClosed }: { registrationClosed: boolean }) {
  return (
    <Box component="section" id="workflow" py={{ xs: 6, md: 9 }}>
      <Container maxWidth="lg">
        <Grid container spacing={{ xs: 3, md: 5 }}>
          <Grid size={{ xs: 12, md: 4 }}>
            <SectionEyebrow icon={<IconRocket size={18} />} label="开通流程" />
            <Typography
              component="h2"
              sx={{
                fontSize: { xs: 30, md: 40 },
                fontWeight: 800,
                lineHeight: 1.15,
                mt: 1.5,
              }}
            >
              从选购到导入节点
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 8 }}>
            <Stack spacing={2}>
              {STEPS.map((step, index) => (
                <Box
                  key={step.title}
                  sx={{
                    display: "grid",
                    gridTemplateColumns: { xs: "44px 1fr", sm: "72px 1fr" },
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      width: 44,
                      height: 44,
                      borderRadius: 1,
                      display: "grid",
                      placeItems: "center",
                      bgcolor: index === 0 && registrationClosed ? "#EAEFF4" : "#5D87FF",
                      color: index === 0 && registrationClosed ? "text.secondary" : "#fff",
                      fontWeight: 800,
                    }}
                  >
                    {index + 1}
                  </Box>
                  <Box
                    sx={{
                      bgcolor: "#fff",
                      border: "1px solid",
                      borderColor: "divider",
                      borderRadius: 1,
                      p: 2.5,
                    }}
                  >
                    <Typography variant="h5">{step.title}</Typography>
                    <Typography variant="body2" color="text.secondary" mt={0.75}>
                      {index === 0 && registrationClosed
                        ? "当前站点未开放新用户注册，已有用户可直接登录购买、续费或管理订阅。"
                        : step.text}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Stack>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

function TrustSection({ telegramLink }: { telegramLink?: string }) {
  return (
    <Box component="section" sx={{ py: { xs: 6, md: 8 }, bgcolor: "#112032", color: "#fff" }}>
      <Container maxWidth="lg">
        <Grid container spacing={3} alignItems="center">
          <Grid size={{ xs: 12, md: 5 }}>
            <SectionEyebrow icon={<IconShieldCheck size={18} />} label="稳定与支持" inverse />
            <Typography
              component="h2"
              sx={{
                fontSize: { xs: 30, md: 40 },
                fontWeight: 800,
                lineHeight: 1.15,
                mt: 1.5,
              }}
            >
              清晰的状态和可靠的售后
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 7 }}>
            <Grid container spacing={2}>
              <TrustItem
                icon={<IconServer size={20} />}
                title="节点状态"
                text="用户可查看可用节点、连接参数和套餐流量使用情况。"
              />
              <TrustItem
                icon={<IconShieldLock size={20} />}
                title="订阅安全"
                text="订阅链接支持重置，降低链接泄露后的持续风险。"
              />
              <TrustItem
                icon={<IconHeadset size={20} />}
                title="售后工单"
                text="节点、订单、套餐和账户问题都可以通过工单进入支持流程。"
              />
              <Grid size={{ xs: 12, sm: 6 }}>
                <Box
                  sx={{
                    border: "1px solid rgba(255,255,255,0.16)",
                    borderRadius: 1,
                    p: 2.5,
                    height: "100%",
                  }}
                >
                  <Typography variant="h5">外部入口</Typography>
                  <Typography variant="body2" color="rgba(255,255,255,0.68)" mt={1}>
                    {telegramLink
                      ? "Telegram 讨论群已配置，可用于接收通知或联系站点支持。"
                      : "未配置外部社群时，页面不会展示无效链接。"}
                  </Typography>
                  {telegramLink ? (
                    <Button
                      component="a"
                      href={telegramLink}
                      target="_blank"
                      rel="noreferrer"
                      variant="outlined"
                      startIcon={<IconBrandTelegram size={18} />}
                      sx={{
                        mt: 2,
                        color: "#fff",
                        borderColor: "rgba(255,255,255,0.4)",
                      }}
                    >
                      Telegram
                    </Button>
                  ) : null}
                </Box>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

function SiteFooter({
  appDescription,
  appName,
  appUrl,
  footer,
  telegramLink,
  tosUrl,
}: {
  appDescription: string;
  appName: string;
  appUrl: string;
  footer: FooterConfig;
  telegramLink?: string;
  tosUrl: string;
}) {
  const currentYear = new Date().getFullYear();
  const description = footer.description || appDescription;
  const copyright = footer.copyright || `Copyright © ${currentYear} ${appName}. All rights reserved.`;
  const links = getFooterLinks(footer, appUrl, tosUrl);
  const contacts = getFooterContacts(footer, telegramLink);
  const seoKeywords = getSeoKeywords(footer, appName);

  return (
    <Box
      component="footer"
      sx={{
        bgcolor: "#fff",
        borderTop: "1px solid",
        borderColor: "divider",
        py: { xs: 4, md: 5 },
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={{ xs: 3, md: 5 }}>
          <Grid size={{ xs: 12, md: 5 }}>
            <Typography variant="h5">{appName}</Typography>
            <Typography variant="body2" color="text.secondary" mt={1.25} maxWidth={460}>
              {description}
            </Typography>
            <Typography variant="body2" color="text.secondary" mt={2}>
              {copyright}
            </Typography>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="subtitle2" fontWeight={700}>
              站点信息
            </Typography>
            <Stack spacing={1} mt={1.5}>
              {links.length ? (
                links.map((item) => <FooterEntry item={item} key={`${item.label}-${item.href || item.text}`} />)
              ) : (
                <Typography variant="body2" color="text.secondary">
                  暂无公开链接。
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                {seoKeywords.join(" / ")}
              </Typography>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Typography variant="subtitle2" fontWeight={700}>
              联系方式
            </Typography>
            <Stack spacing={1} mt={1.5}>
              {contacts.map((item) => (
                <FooterEntry item={item} key={`${item.label}-${item.href || item.text}`} />
              ))}
              <Typography variant="body2" color="text.secondary">
                SEO：{seoKeywords.join("，")}
              </Typography>
            </Stack>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

function FooterEntry({ item }: { item: FooterItemConfig }) {
  if (item.href) {
    return <FooterLink href={item.href} label={item.label} />;
  }

  return (
    <Typography variant="body2" color="text.secondary">
      {item.label}
      {item.text ? `：${item.text}` : ""}
    </Typography>
  );
}

function FooterLink({ href, label }: { href: string; label: string }) {
  return (
    <Typography
      component="a"
      href={href}
      target="_blank"
      rel="noreferrer"
      variant="body2"
      color="text.secondary"
      sx={{ textDecoration: "none", "&:hover": { color: "primary.main" } }}
    >
      {label}
    </Typography>
  );
}

function getFooterLinks(footer: FooterConfig, appUrl: string, tosUrl: string): FooterItemConfig[] {
  if (footer.links?.length) {
    return footer.links;
  }

  const links: FooterItemConfig[] = [];
  if (appUrl) {
    links.push({ label: "官方网站", href: appUrl });
  }
  if (tosUrl) {
    links.push({ label: "服务条款", href: tosUrl });
  }
  return links;
}

function getFooterContacts(footer: FooterConfig, telegramLink?: string): FooterItemConfig[] {
  if (footer.contacts?.length) {
    return footer.contacts;
  }

  if (telegramLink) {
    return [{ label: "Telegram 讨论群", href: telegramLink }];
  }

  return [{ label: "工单支持", text: "请通过账户中心工单联系支持。" }];
}

function getSeoKeywords(footer: FooterConfig, appName: string): string[] {
  if (footer.seoKeywords?.length) {
    return footer.seoKeywords;
  }

  return [appName, "VPN", "代理节点", "订阅节点", "套餐流量", "多端客户端", "工单支持"];
}

function getLandingDescription(appDescription: string): string {
  const normalized = appDescription.trim();
  if (!normalized || normalized === DEFAULT_PANEL_DESCRIPTION) {
    return DEFAULT_SERVICE_DESCRIPTION;
  }
  return normalized;
}

function SectionEyebrow({ icon, inverse, label }: { icon: ReactNode; inverse?: boolean; label: string }) {
  return (
    <Stack direction="row" spacing={1} alignItems="center" color={inverse ? "#D8FFF7" : "primary.main"}>
      {icon}
      <Typography variant="subtitle2" fontWeight={700}>
        {label}
      </Typography>
    </Stack>
  );
}

function CheckLine({ children }: { children: ReactNode }) {
  return (
    <Stack direction="row" spacing={1.25} alignItems="flex-start">
      <Box color="success.main" mt={0.15}>
        <IconCheck size={18} />
      </Box>
      <Typography variant="body2" color="text.secondary">
        {children}
      </Typography>
    </Stack>
  );
}

function PreviewAction({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <Stack
      direction="row"
      spacing={0.75}
      alignItems="center"
      sx={{
        px: 1.25,
        py: 0.75,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        color: "text.secondary",
      }}
    >
      {icon}
      <Typography variant="caption" fontWeight={700}>
        {label}
      </Typography>
    </Stack>
  );
}

function PreviewSummary({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <Grid size={{ xs: 12, sm: 4 }}>
      <Stack direction="row" spacing={1.25} alignItems="center">
        <Box color="primary.main">{icon}</Box>
        <Box>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="h6">{value}</Typography>
        </Box>
      </Stack>
    </Grid>
  );
}

function TrustItem({ icon, text, title }: { icon: ReactNode; text: string; title: string }) {
  return (
    <Grid size={{ xs: 12, sm: 6 }}>
      <Box
        sx={{
          border: "1px solid rgba(255,255,255,0.16)",
          borderRadius: 1,
          p: 2.5,
          height: "100%",
        }}
      >
        <Box color="#13DEB9">{icon}</Box>
        <Typography variant="h5" mt={1.25}>
          {title}
        </Typography>
        <Typography variant="body2" color="rgba(255,255,255,0.68)" mt={1}>
          {text}
        </Typography>
      </Box>
    </Grid>
  );
}
