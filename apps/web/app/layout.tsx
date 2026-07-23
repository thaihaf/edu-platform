import "./globals.css";
import { Providers } from "@/components/providers";
export const metadata = {
  title: "Research Studio",
  description: "Administrative research and course studio",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
