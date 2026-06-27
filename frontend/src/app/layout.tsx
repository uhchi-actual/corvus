import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Corvus",
  description: "SQL-first OBD-II diagnostic dashboard.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className="corvusRoot">
      <body className="corvusBody">{children}</body>
    </html>
  );
}
