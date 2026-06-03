import type { Metadata } from "next";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "THWS — Energie-Anomalien",
  description: "Kostenpriorisierte Übersicht der Energie-Anomalien",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body className="antialiased">
        <Providers>
          <div className="mx-auto max-w-[1100px] px-6 py-8">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
