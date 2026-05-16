import { Box, Stack, styled, Typography } from "@mui/material";
import Link from "next/link";
import { useSiteConfig } from "@/contexts/SiteConfigContext";

const LinkStyled = styled(Link)(() => ({
  height: "70px",
  width: "180px",
  overflow: "hidden",
  display: "flex",
  alignItems: "center",
  textDecoration: "none",
}));

const Logo = () => {
  const { appName, logo } = useSiteConfig();

  return (
    <LinkStyled href="/">
      {logo ? (
        <Box
          component="img"
          src={logo}
          alt={appName}
          sx={{
            maxHeight: 48,
            maxWidth: 160,
            objectFit: "contain",
          }}
        />
      ) : (
        <Stack>
          <Typography variant="h4" color="primary.main" lineHeight={1}>
            {appName}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            用户中心
          </Typography>
        </Stack>
      )}
    </LinkStyled>
  );
};

export default Logo;
