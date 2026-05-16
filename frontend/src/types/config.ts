export type FooterItemConfig = {
  label: string;
  href?: string;
  text?: string;
};

export type FooterConfig = {
  description?: string;
  copyright?: string;
  seoKeywords?: string[];
  links?: FooterItemConfig[];
  contacts?: FooterItemConfig[];
};

export type RuntimeConfig = {
  apiBaseUrl?: string;
  footer?: FooterConfig;
};
