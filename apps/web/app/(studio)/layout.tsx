import { StudioShell } from "@/components/studio-shell";
export default function Layout({ children }: { children: React.ReactNode }) {
  return <StudioShell>{children}</StudioShell>;
}
