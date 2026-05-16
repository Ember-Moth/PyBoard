import { Avatar, Box, Button, IconButton, ListItemIcon, ListItemText, Menu, MenuItem } from "@mui/material";
import { IconLogout, IconSettings, IconUser } from "@tabler/icons-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { clearAuthToken } from "@/lib/auth";

const Profile = () => {
  const router = useRouter();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleLogout = () => {
    clearAuthToken();
    setAnchorEl(null);
    router.replace("/auth/login");
  };

  return (
    <Box>
      <IconButton
        size="large"
        aria-label="account menu"
        color="inherit"
        onClick={(event) => setAnchorEl(event.currentTarget)}
        sx={{ ...(anchorEl && { color: "primary.main" }) }}
      >
        <Avatar src="/images/profile/user-1.jpg" alt="用户头像" sx={{ width: 35, height: 35 }} />
      </IconButton>
      <Menu
        id="account-menu"
        anchorEl={anchorEl}
        keepMounted
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        sx={{ "& .MuiMenu-paper": { width: "200px" } }}
      >
        <MenuItem onClick={() => router.push("/settings")}>
          <ListItemIcon>
            <IconUser width={20} />
          </ListItemIcon>
          <ListItemText>账户资料</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => router.push("/settings")}>
          <ListItemIcon>
            <IconSettings width={20} />
          </ListItemIcon>
          <ListItemText>账户设置</ListItemText>
        </MenuItem>
        <Box mt={1} py={1} px={2}>
          <Button
            variant="outlined"
            color="primary"
            fullWidth
            startIcon={<IconLogout size={18} />}
            onClick={handleLogout}
          >
            退出登录
          </Button>
        </Box>
      </Menu>
    </Box>
  );
};

export default Profile;
