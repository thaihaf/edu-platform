export type Role =
  "ADMIN" | "RESEARCHER" | "REVIEWER" | "EDITOR" | "VIEWER" | "LEARNER";
export type CurrentUser = {
  id: string;
  name: string;
  roles: Role[];
  token?: string;
};
export const mockUser: CurrentUser = {
  id: "00000000-0000-0000-0000-000000000001",
  name: "Development Admin",
  roles: ["ADMIN", "RESEARCHER", "REVIEWER", "EDITOR"],
};
export function may(user: CurrentUser | undefined, roles: Role[]) {
  return Boolean(user?.roles.some((role) => roles.includes(role)));
}
