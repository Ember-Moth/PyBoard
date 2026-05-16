import { Stack, styled, Typography } from "@mui/material";
import Link from "next/link";

const LinkStyled = styled(Link)(() => ({
  height: "70px",
  width: "180px",
  overflow: "hidden",
  display: "flex",
  alignItems: "center",
  textDecoration: "none",
}));

const Logo = () => {
  return (
    <LinkStyled href="/">
      <Stack>
        <Typography variant="h4" color="primary.main" lineHeight={1}>
          PyBoard
        </Typography>
        <Typography variant="caption" color="text.secondary">
          用户中心
        </Typography>
      </Stack>
    </LinkStyled>
  );
};

export default Logo;
