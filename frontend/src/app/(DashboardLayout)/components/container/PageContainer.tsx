// import { Helmet } from 'react-helmet';
import type { ReactNode } from "react";

type Props = {
  description?: string;
  children: ReactNode;
  title?: string;
};

const PageContainer = ({ title, description, children }: Props) => (
  <div>
    <title>{title}</title>
    <meta name="description" content={description} />

    {children}
  </div>
);

export default PageContainer;
