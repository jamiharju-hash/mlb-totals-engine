import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MLB Projection Dashboard",
  description: "MLB projections, edges, ROI and model metrics"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
