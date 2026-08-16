import type { Metadata } from "next";
import { LandingClient } from "./LandingClient";

export const metadata: Metadata = {
  // `absolute` because the root layout appends "· Numerate" to every title,
  // which would brand this one twice.
  title: {
    absolute: "Numerate — Ask your spreadsheet anything, then check the answer",
  },
  description:
    "Upload a file or connect a Google Sheet, ask questions in plain English, and click any figure to see the formula and the exact rows behind it.",
};

export default function LandingPage() {
  return <LandingClient />;
}
