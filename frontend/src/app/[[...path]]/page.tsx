import App from "@/app/App";

export const dynamic = "force-static";

export function generateStaticParams() {
  return [{ path: [] }];
}

export default function Page() {
  return <App />;
}
