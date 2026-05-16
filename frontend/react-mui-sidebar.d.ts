declare module "react-mui-sidebar" {
  import type { ComponentType } from "react";

  type SidebarComponentProps = Record<string, unknown>;

  // Declare the component or types provided by the module here
  const Sidebar: ComponentType<SidebarComponentProps>;
  const Logo: ComponentType<SidebarComponentProps>;
  const Menu: ComponentType<SidebarComponentProps>;
  const MenuItem: ComponentType<SidebarComponentProps>;
  const Submenu: ComponentType<SidebarComponentProps>;

  export { Logo, Menu, MenuItem, Sidebar, Submenu };
}
