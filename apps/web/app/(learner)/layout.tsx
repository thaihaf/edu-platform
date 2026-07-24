import { LearnerShell } from "@/components/learner";
export default function Layout({ children }: { children: React.ReactNode }) {
  return <LearnerShell>{children}</LearnerShell>;
}
