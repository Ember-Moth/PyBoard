import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box } from "@mui/material";
import { IconPoint } from "@tabler/icons-react";
import { Logo, Menu, MenuItem, Sidebar as MUI_Sidebar, Submenu } from "react-mui-sidebar";

import Menuitems from "./MenuItems";

const renderMenuItems = (items: any[], pathDirect: string) => {
  return items.map((item: any) => {
    const Icon = item.icon ? item.icon : IconPoint;
    const itemIcon = <Icon stroke={1.5} size="1.3rem" />;

    if (item.subheader) {
      return <Menu subHeading={item.subheader} key={item.subheader} />;
    }

    if (item.children) {
      return (
        <Submenu key={item.id} title={item.title} icon={itemIcon} borderRadius="7px">
          {renderMenuItems(item.children, pathDirect)}
        </Submenu>
      );
    }

    return (
      <Box px={3} key={item.id}>
        <MenuItem
          isSelected={pathDirect === item?.href}
          borderRadius="8px"
          icon={itemIcon}
          link={item.href}
          component={Link}
        >
          {item.title}
        </MenuItem>
      </Box>
    );
  });
};

const SidebarItems = () => {
  const pathname = usePathname();

  return (
    <MUI_Sidebar width="100%" showProfile={false} themeColor="#5D87FF" themeSecondaryColor="#49beff">
      <Logo component={Link} to="/">
        PyBoard
      </Logo>
      {renderMenuItems(Menuitems, pathname)}
    </MUI_Sidebar>
  );
};

export default SidebarItems;
