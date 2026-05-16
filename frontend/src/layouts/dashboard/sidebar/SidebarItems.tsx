import { Box } from "@mui/material";
import { IconPoint } from "@tabler/icons-react";
import { type AnchorHTMLAttributes, type ComponentType, forwardRef, type MouseEvent } from "react";
import { Menu, MenuItem, Sidebar as MUI_Sidebar, Logo as SidebarLogo, Submenu } from "react-mui-sidebar";
import { useSiteConfig } from "@/contexts/SiteConfigContext";
import { navigateSpa, useSpaPathname } from "@/lib/spa-navigation";

import Menuitems from "./MenuItems";

type SidebarIcon = ComponentType<{ stroke?: number; size?: number | string }>;

type SidebarMenuItem = {
  navlabel?: boolean;
  subheader?: string;
  id?: string;
  title?: string;
  icon?: SidebarIcon;
  href?: string;
  children?: SidebarMenuItem[];
};

type SpaLinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  to?: string;
};

const SpaLink = forwardRef<HTMLAnchorElement, SpaLinkProps>(({ href, onClick, target, to, ...props }, ref) => {
  const destination = href || to || "#";

  const handleClick = (event: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(event);
    if (shouldUseBrowserNavigation(event, target)) {
      return;
    }

    if (navigateSpa(destination)) {
      event.preventDefault();
    }
  };

  return <a ref={ref} href={destination} target={target} onClick={handleClick} {...props} />;
});

SpaLink.displayName = "SpaLink";

const renderMenuItems = (items: SidebarMenuItem[], pathDirect: string) => {
  return items.map((item) => {
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
          link={item.href || "#"}
          component={SpaLink}
        >
          {item.title}
        </MenuItem>
      </Box>
    );
  });
};

const SidebarItems = () => {
  const pathname = useSpaPathname();
  const { appName, logo } = useSiteConfig();

  return (
    <MUI_Sidebar width="100%" showProfile={false} themeColor="#5D87FF" themeSecondaryColor="#49beff">
      <SidebarLogo component={SpaLink} href="/dashboard">
        {logo ? (
          <Box component="img" src={logo} alt={appName} sx={{ maxHeight: 40, maxWidth: 150, objectFit: "contain" }} />
        ) : (
          appName
        )}
      </SidebarLogo>
      {renderMenuItems(Menuitems, pathname)}
    </MUI_Sidebar>
  );
};

export default SidebarItems;

function shouldUseBrowserNavigation(event: MouseEvent<HTMLAnchorElement>, target?: string): boolean {
  return (
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.altKey ||
    event.ctrlKey ||
    event.shiftKey ||
    target === "_blank"
  );
}
