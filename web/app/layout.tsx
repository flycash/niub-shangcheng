import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "牛掰商城",
  description: "有温度的日常好物商城",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
