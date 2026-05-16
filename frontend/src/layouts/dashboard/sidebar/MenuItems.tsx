import {
  IconCreditCard,
  IconHeadset,
  IconKey,
  IconLayoutDashboard,
  IconReceipt2,
  IconSettings,
  IconShare3,
} from "@tabler/icons-react";
import { uniqueId } from "lodash";

const Menuitems = [
  {
    navlabel: true,
    subheader: "账户",
  },
  {
    id: uniqueId(),
    title: "仪表盘",
    icon: IconLayoutDashboard,
    href: "/dashboard",
  },
  {
    id: uniqueId(),
    title: "我的订阅",
    icon: IconKey,
    href: "/subscribe",
  },
  {
    id: uniqueId(),
    title: "购买套餐",
    icon: IconCreditCard,
    href: "/plans",
  },
  {
    navlabel: true,
    subheader: "服务",
  },
  {
    id: uniqueId(),
    title: "我的订单",
    icon: IconReceipt2,
    href: "/orders",
  },
  {
    id: uniqueId(),
    title: "工单支持",
    icon: IconHeadset,
    href: "/tickets",
  },
  {
    id: uniqueId(),
    title: "邀请返佣",
    icon: IconShare3,
    href: "/invite",
  },
  {
    id: uniqueId(),
    title: "账户设置",
    icon: IconSettings,
    href: "/settings",
  },
];

export default Menuitems;
