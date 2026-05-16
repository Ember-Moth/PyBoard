import React from "react";
import { AppBar, Badge, Box, IconButton, Stack, styled, Toolbar, Typography } from "@mui/material";
import { IconBellRinging, IconMenu } from "@tabler/icons-react";

import Profile from "./Profile";

interface ItemType {
  toggleMobileSidebar: (event: React.MouseEvent<HTMLElement>) => void;
}

const AppBarStyled = styled(AppBar)(({ theme }) => ({
  boxShadow: "none",
  background: theme.palette.background.paper,
  justifyContent: "center",
  backdropFilter: "blur(4px)",
  [theme.breakpoints.up("lg")]: {
    minHeight: "70px",
  },
}));

const ToolbarStyled = styled(Toolbar)(({ theme }) => ({
  width: "100%",
  color: theme.palette.text.secondary,
}));

const Header = ({ toggleMobileSidebar }: ItemType) => {
  return (
    <AppBarStyled position="sticky" color="default">
      <ToolbarStyled>
        <IconButton
          color="inherit"
          aria-label="menu"
          onClick={toggleMobileSidebar}
          sx={{ display: { lg: "none", xs: "inline" } }}
        >
          <IconMenu width="20" height="20" />
        </IconButton>
        <IconButton size="large" aria-label="notifications" color="inherit">
          <Badge variant="dot" color="primary">
            <IconBellRinging size="21" stroke="1.5" />
          </Badge>
        </IconButton>
        <Box flexGrow={1} />
        <Stack spacing={1.5} direction="row" alignItems="center">
          <Typography variant="body2" color="text.secondary" sx={{ display: { xs: "none", sm: "block" } }}>
            用户中心
          </Typography>
          <Profile />
        </Stack>
      </ToolbarStyled>
    </AppBarStyled>
  );
};

export default Header;
