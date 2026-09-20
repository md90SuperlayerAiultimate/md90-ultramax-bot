import { trpc } from "@/lib/trpc";

export default function AuthenticatedScopeBadge({ compact = false }: { compact?: boolean }) {
  const { data: user, isLoading: userLoading, isError: userError } = trpc.auth.me.useQuery(undefined, { staleTime: 30_000 });
  const authenticated = Boolean(user?.openId);
  const paper = trpc.paper.overview.useQuery(undefined, { enabled: authenticated, staleTime: 15_000 });
  const shadow = trpc.shadow.observations.useQuery(undefined, { enabled: authenticated, staleTime: 15_000 });
  const news = trpc.intel.news.useQuery(undefined, { enabled: authenticated, staleTime: 15_000 });
  const state = userLoading || (authenticated && (paper.isLoading || shadow.isLoading || news.isLoading)) ? "CHECKING" : userError || paper.isError || shadow.isError || news.isError ? "ERROR" : authenticated ? "AUTHENTICATED" : "DEMO SESSION";
  const detail = authenticated ? `paper ${paper.data ? "READ / WRITE" : "PENDING"} · shadow ${shadow.data ? "REFRESHED" : "PENDING"} · news ${news.data ? "REFRESHED" : "PENDING"}` : user?.email ?? (userError ? "session unavailable" : "user-scope read pending");
  return (
    <span className={`authenticated-scope-badge ${compact ? "compact" : ""}`} title={`${state} · ${detail}`} aria-label={`Authenticated scope ${state}; ${detail}`}>
      <span className={`status-dot ${state === "AUTHENTICATED" ? "teal" : state === "ERROR" ? "vermillion" : "amber"}`} />
      <span>{compact ? state : `SCOPE / ${state}`}</span>
      {!compact && <small>{detail}</small>}
    </span>
  );
}
