"use client";

import type { ReactNode } from "react";
import { useSiteConfig } from "@/contexts/SiteConfigContext";

type Props = {
  description?: string;
  children: ReactNode;
  keywords?: string | string[];
  title?: string;
};

const PageContainer = ({ title, description, keywords, children }: Props) => {
  const { appName, appDescription } = useSiteConfig();
  const pageTitle = title ? `${title} - ${appName}` : appName;
  const metaDescription = appDescription || description || "";
  const metaKeywords = Array.isArray(keywords) ? keywords.join(",") : keywords;

  return (
    <div>
      <title>{pageTitle}</title>
      <meta name="description" content={metaDescription} />
      {metaKeywords ? <meta name="keywords" content={metaKeywords} /> : null}

      {children}
    </div>
  );
};

export default PageContainer;
