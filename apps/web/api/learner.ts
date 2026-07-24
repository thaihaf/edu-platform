/** Learner contracts deliberately omit answer keys and reviewer metadata. */
export type LearnerCourse = {
  id: string;
  versionId: string;
  title: string;
  description: string;
  difficulty: string;
  duration: string;
  modules: number;
  lessons: number;
  progress: number;
  status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";
};
export type LearnerCitation = {
  label: string;
  title: string;
  publisher: string;
  section?: string;
  sourceType: string;
  publishedAt?: string;
  url?: string;
};
export type LearnerQuestion = {
  id: string;
  type: "SINGLE_CHOICE" | "SHORT_ANSWER" | "INTERVIEW";
  stem: string;
  options?: { id: string; label: string }[];
  origin: string;
  citation: LearnerCitation;
};
export const learnerKeys = {
  courses: (learnerId: string) => ["learner", learnerId, "courses"] as const,
  course: (learnerId: string, courseId: string, versionId: string) =>
    ["learner", learnerId, "course", courseId, versionId] as const,
  session: (learnerId: string, mode: string, sessionId: string) =>
    ["learner", learnerId, mode, sessionId] as const,
  skills: (learnerId: string) => ["learner", learnerId, "skills"] as const,
};
export const learnerPaths = {
  courses: "/learner/courses",
  progress: "/learner/me/progress",
  practice: "/learner/practice-sessions",
  exams: "/learner/exam-sessions",
  flashcards: "/learner/flashcard-decks",
  interviews: "/learner/interview-sessions",
} as const;
export const demoCourse: LearnerCourse = {
  id: "published-web-foundations",
  versionId: "course-v1",
  title: "Web foundations",
  description:
    "Learn accessible, secure web delivery from published course material.",
  difficulty: "Intermediate",
  duration: "2 hours",
  modules: 2,
  lessons: 3,
  progress: 33,
  status: "IN_PROGRESS",
};
export const demoQuestion: LearnerQuestion = {
  id: "question-v1",
  type: "SINGLE_CHOICE",
  stem: "Which HTML element gives a page its primary heading?",
  options: [
    { id: "a", label: "<h1>" },
    { id: "b", label: "<div>" },
    { id: "c", label: "<span>" },
  ],
  origin: "Domain standard",
  citation: {
    label: "HTML semantics",
    title: "HTML Standard",
    publisher: "WHATWG",
    section: "The h1 element",
    sourceType: "Standard",
    url: "https://html.spec.whatwg.org/",
  },
};
