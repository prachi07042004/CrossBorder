export const metadata = {
  title: "AI Cross-Border Tax & Compliance System",
  description: "Educational prototype. Not legally binding tax advice.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
