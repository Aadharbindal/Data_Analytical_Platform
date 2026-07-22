import { SharedDashboardClient } from "./SharedDashboardClient";

export default async function SharedDashboardPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <SharedDashboardClient token={token} />;
}
