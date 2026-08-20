import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "AI DevOps Agent",
  description: "Read-only AI infrastructure diagnostics",
};

const themeScript = `
(() => {
  try {
    const stored = window.localStorage.getItem("dashboard-theme");
    const theme = stored === "light" || stored === "dark"
      ? stored
      : (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    document.documentElement.dataset.theme = theme;
  } catch {
    document.documentElement.dataset.theme = "dark";
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        {children}
      </body>
    </html>
  );
}
