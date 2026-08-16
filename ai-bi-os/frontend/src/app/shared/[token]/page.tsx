import type { Metadata } from "next";
import { SharedDashboardClient } from "./SharedDashboardClient";

// Deliberately not fetching the dashboard to name it in the preview.
//
// Privacy: a link can be password protected, and the whole point of that is
// that the dataset stays hidden until the password is entered. Putting its
// name in an OG tag would hand it to anyone the link is forwarded to, and to
// every crawler, without the password ever being typed.
//
// Reliability: the API runs on a free instance that cold-starts in ~37s.
// Crawlers give up in a couple of seconds, so a fetch here would usually just
// time out and produce no preview at all — worse than a good generic one.
export async function generateMetadata(): Promise<Metadata> {
  const title = "Shared dashboard";
  const description =
    "A read-only view of verified metrics and insights, shared from Numerate.";

  // The image has to be named again here. Declaring an `openGraph` object on a
  // segment replaces the parent's rather than merging into it, so the root
  // opengraph-image.tsx that every other route inherits was being dropped and
  // these links previewed as text with no card image at all.
  const image = "/opengraph-image";

  return {
    title,
    description,
    openGraph: { title: `${title} · Numerate`, description, images: [image] },
    twitter: {
      card: "summary_large_image",
      title: `${title} · Numerate`,
      description,
      images: [image],
    },
    // These links are handed out privately. Keeping them out of search results
    // means a forwarded dashboard can't later surface to strangers via Google.
    robots: { index: false, follow: false },
  };
}

export default async function SharedDashboardPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <SharedDashboardClient token={token} />;
}
