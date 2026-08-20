import "./globals.css";

export const metadata = {
  title: "AI DevOps Agent",
  description: "Read-only AI infrastructure diagnostics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
