import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { trpc } from "@/lib/trpc";

function AuditCard({ label, value, detail, tone = "default" }: { label: string; value: string; detail: string; tone?: "default" | "good" | "locked" }) {
  const toneClass = tone === "good" ? "text-primary" : tone === "locked" ? "text-amber-300" : "text-foreground";
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
      <strong className={`mt-2 block text-lg ${toneClass}`}>{value}</strong>
      <span className="mt-1 block text-xs text-muted-foreground">{detail}</span>
    </div>
  );
}

export default function AuthenticatedAudit() {
  const [language, setLanguage] = useState<"ID" | "EN">("ID");
  const { data: user, isLoading: userLoading } = trpc.auth.me.useQuery();
  const authenticated = Boolean(user?.openId);
  const paper = trpc.paper.overview.useQuery(undefined, { enabled: authenticated });
  const shadow = trpc.shadow.observations.useQuery(undefined, { enabled: authenticated });
  const news = trpc.intel.news.useQuery(undefined, { enabled: authenticated });
  const id = language === "ID";
  const copy = id ? {
    eyebrow: "/ MD90 AUTHENTICATED AUDIT", title: "Verifikasi persistence & akses", intro: "Surface E2E terproteksi. Semua hasil dibaca dari sesi authenticated dan prosedur PAPER/SHADOW canonical; tidak ada otoritas live.", status: "Status audit authenticated", session: "Sesi", paper: "Persistensi paper", shadow: "Refresh shadow", live: "Route live", pending: "query terproteksi belum selesai", noRoute: "signing · withdrawal · network order off", userScope: "/ USER-SCOPE CHECK", paperWrite: "Penulisan paper canonical", paperDesc: "Sesi terproteksi memanggil overview paper yang sama dan menyimpan user scope authenticated. Ini memverifikasi write path tanpa menambah route transaksi baru.", identity: "Identitas", paperState: "Status paper", timeframe: "Timeframe dasar", ledger: "Kontrak ledger", immutable: "immutable / paper", lineage: "/ SHADOW + NEWS CHECK", refresh: "Lineage refresh", refreshDesc: "Prosedur shadow dan intelligence hanya berjalan dalam mode observasi. Hasil disimpan dengan metadata sumber/freshness dan tidak dapat mempromosikan order live.", newsItems: "Item berita", orderRoute: "Route order", safety: "Tidak ada API key, seed phrase, private key, signing, deposit, withdrawal, atau network order yang diterima halaman ini. Query error tetap terlihat sebagai kegagalan audit; tidak pernah diubah menjadi pass palsu.", toggle: "Ganti bahasa" 
  } : {
    eyebrow: "/ MD90 AUTHENTICATED AUDIT", title: "Persistence & access verification", intro: "Protected E2E surface. Every result below is read from the authenticated session and canonical PAPER/SHADOW procedures; no live authority is attached.", status: "Authenticated audit status", session: "Session", paper: "Paper persistence", shadow: "Shadow refresh", live: "Live route", pending: "protected query not complete", noRoute: "signing · withdrawal · network order off", userScope: "/ USER-SCOPE CHECK", paperWrite: "Canonical paper write", paperDesc: "The protected session calls the same paper overview that persists the authenticated user scope. This verifies the write path without adding a new transaction route.", identity: "Identity", paperState: "Paper state", timeframe: "Base timeframe", ledger: "Ledger contract", immutable: "immutable / paper", lineage: "/ SHADOW + NEWS CHECK", refresh: "Refresh lineage", refreshDesc: "Shadow and intelligence procedures execute only in observation mode. Their results are retained with source/freshness metadata and cannot promote a live order.", newsItems: "News items", orderRoute: "Order route", safety: "No API key, seed phrase, private key, signing, deposit, withdrawal, or network order is accepted by this page. A query error remains visible as an audit failure; it is never converted into a false pass.", toggle: "Toggle language"
  };

  const paperState = paper.isLoading ? "CHECKING" : paper.isError ? "ERROR" : paper.data ? "READ / WRITE" : "PENDING";
  const shadowState = shadow.isLoading ? "CHECKING" : shadow.isError ? "ERROR" : shadow.data ? "REFRESHED" : "PENDING";
  const newsState = news.isLoading ? "CHECKING" : news.isError ? "ERROR" : news.data ? "REFRESHED" : "PENDING";
  const latestPaper = paper.data?.generatedAt ? new Date(paper.data.generatedAt).toLocaleTimeString() : "—";

  return (
    <DashboardLayout>
      <main className="min-h-screen bg-background p-6 text-foreground md:p-10">
        <div className="mx-auto max-w-5xl space-y-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">{copy.eyebrow}</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">{copy.title}</h1>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">{copy.intro}</p>
            </div>
            <button className="rounded-md border border-border px-3 py-2 text-xs font-semibold tracking-[0.14em] text-muted-foreground transition hover:border-primary hover:text-primary" onClick={() => setLanguage(id ? "EN" : "ID")} aria-label={copy.toggle}>{language}</button>
          </div>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label={copy.status}>
            <AuditCard label={copy.session} value={userLoading ? "CHECKING" : authenticated ? "AUTHENTICATED" : "UNAUTHENTICATED"} detail={user?.name ?? "OAuth identity pending"} tone={authenticated ? "good" : "default"} />
            <AuditCard label={copy.paper} value={paperState} detail={paper.data ? `overview ${latestPaper}` : copy.pending} tone={paper.data ? "good" : "default"} />
            <AuditCard label={copy.shadow} value={shadowState} detail={shadow.data ? `${shadow.data.observations.length} observations · no order route` : copy.pending} tone={shadow.data ? "good" : "default"} />
            <AuditCard label={copy.live} value="DISABLED" detail={copy.noRoute} tone="locked" />
          </section>

          <section className="grid gap-3 md:grid-cols-2" aria-label={id ? "Pemeriksaan data authenticated" : "Authenticated data checks"}>
            <div className="rounded-lg border border-border bg-card p-5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">{copy.userScope}</p>
              <h2 className="mt-2 text-xl font-semibold">{copy.paperWrite}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{copy.paperDesc}</p>
              <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
                <div><dt className="text-xs text-muted-foreground">{copy.identity}</dt><dd className="mt-1 font-medium">{user?.email ?? "—"}</dd></div>
                <div><dt className="text-xs text-muted-foreground">{copy.paperState}</dt><dd className="mt-1 font-medium text-primary">{paperState}</dd></div>
                <div><dt className="text-xs text-muted-foreground">{copy.timeframe}</dt><dd className="mt-1 font-medium">{paper.data?.timeframe ?? "—"}</dd></div>
                <div><dt className="text-xs text-muted-foreground">{copy.ledger}</dt><dd className="mt-1 font-medium">{copy.immutable}</dd></div>
              </dl>
            </div>
            <div className="rounded-lg border border-border bg-card p-5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">{copy.lineage}</p>
              <h2 className="mt-2 text-xl font-semibold">{copy.refresh}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{copy.refreshDesc}</p>
              <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
                <div><dt className="text-xs text-muted-foreground">Shadow</dt><dd className="mt-1 font-medium text-primary">{shadowState}</dd></div>
                <div><dt className="text-xs text-muted-foreground">News</dt><dd className="mt-1 font-medium text-primary">{newsState}</dd></div>
                <div><dt className="text-xs text-muted-foreground">{copy.newsItems}</dt><dd className="mt-1 font-medium">{news.data?.items.length ?? "—"}</dd></div>
                <div><dt className="text-xs text-muted-foreground">{copy.orderRoute}</dt><dd className="mt-1 font-medium text-amber-300">DISABLED</dd></div>
              </dl>
            </div>
          </section>

          <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 text-sm text-muted-foreground">{copy.safety}</div>
        </div>
      </main>
    </DashboardLayout>
  );
}
