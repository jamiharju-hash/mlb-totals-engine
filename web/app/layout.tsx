import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MLB Projection Dashboard",
  description: "MLB betting projections, team ROI, edge and override dashboard"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
