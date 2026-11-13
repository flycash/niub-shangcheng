import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "牛掰商城 · 运营后台",
  description: "牛掰商城内部运营管理后台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="admin-header">
          <div className="admin-header__inner">
            <Link className="admin-brand" href="/conversations">
              <span>NIUB</span>
              <strong>运营后台</strong>
            </Link>
            <nav aria-label="后台导航">
              <Link href="/conversations">对话管理</Link>
            </nav>
            <div className="environment-pill">
              <i />
              INTERNAL
            </div>
          </div>
        </header>
        <main className="admin-main">{children}</main>
      </body>
    </html>
  );
}
