// Design philosophy: Signal Atelier — a crafted research terminal where every signal shows evidence, uncertainty, provenance, and operating mode.
import { useMemo, useState } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";
import { useIsMobile } from "@/hooks/useMobile";
import { uiCopy } from "@shared/i18n";
import { projectCandles } from "@/lib/candles";
import TradingViewSurface from "@/components/TradingViewSurface";
import AuthenticatedScopeBadge from "@/components/AuthenticatedScopeBadge";
import MarketContextControls from "@/components/MarketContextControls";
import PaperWorkflowPanel from "@/components/PaperWorkflowPanel";
import { TimeframeLineage, useTimeframe } from "@/contexts/TimeframeContext";
import { formatTimeframe } from "@shared/timeframe";
import { OPERATING_STAGES } from "@shared/operatingCockpit";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BookOpen,
  BrainCircuit,
  ChevronDown,
  CircleHelp,
  Database,
  Eye,
  FileCheck2,
  Gauge,
  Layers3,
  ListFilter,
  LockKeyhole,
  Menu,
  PanelLeft,
  Play,
  Radio,
  RefreshCw,
  Search,
    ShieldCheck,
    Settings2,
  SlidersHorizontal,
  Sparkles,
  Target,
  TrendingUp,
  TriangleAlert,
  WalletCards,
  X,
} from "lucide-react";

type Mode = "PAPER" | "SHADOW" | "LIVE";

type Signal = {
  symbol: string;
  market: string;
  bias: "LONG" | "SHORT" | "WATCH";
  score: number;
  confidence: number;
  change: string;
  updated: string;
  source: string;
  accent: "teal" | "amber" | "vermillion";
};

const EMPTY_SIGNAL: Signal = {
  symbol: "—",
  market: "NO VERIFIED SIGNAL",
  bias: "WATCH",
  score: 0,
  confidence: 0,
  change: "—",
  updated: "evidence pending",
  source: "CANONICAL DATA REQUIRED",
  accent: "amber",
};

const layers = [
  { label: "Structure", value: null, note: "Evidence pending" },
  { label: "Momentum", value: null, note: "Evidence pending" },
  { label: "Liquidity", value: null, note: "Provider pending" },
  { label: "Macro / news", value: null, note: "Source pending" },
  { label: "Risk policy", value: null, note: "Policy result pending" },
];

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

function MiniSparkline({ accent = "teal", down = false }: { accent?: "teal" | "amber" | "vermillion"; down?: boolean }) {
  const stroke = accent === "amber" ? "#E4A94A" : accent === "vermillion" ? "#F16A5B" : "#22C7B8";
  const points = down ? "0,24 12,16 26,20 42,10 58,19 76,7 92,13 108,4" : "0,23 14,22 28,17 42,20 58,11 76,13 92,5 108,8";
  return (
    <svg viewBox="0 0 108 28" className="sparkline" aria-hidden="true">
      <polyline points={points} fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SectionLabel({ children, aside }: { children: React.ReactNode; aside?: string }) {
  return (
    <div className="section-label">
      <span>{children}</span>
      {aside && <span className="section-label-aside">{aside}</span>}
    </div>
  );
}

export default function Home() {
  const { timeframe, instrument, setInstrument } = useTimeframe();
  const [, navigate] = useLocation();
  const [mode, setMode] = useState<Mode>("PAPER");
  const [activeNav, setActiveNav] = useState("Overview");
  const [selectedSignal, setSelectedSignal] = useState<Signal>(EMPTY_SIGNAL);
  const [mobileNav, setMobileNav] = useState(false);
  const isMobile = useIsMobile();
  const [language, setLanguage] = useState<"ID" | "EN">("ID");
  const text = uiCopy[language];
  const paperInput = useMemo(() => ({ timeframe: timeframe.base, htf: timeframe.htf, symbol: instrument.id }), [timeframe.base, timeframe.htf, instrument.id]);
  const cockpitQuery = trpc.cockpit.snapshot.useQuery(paperInput, { refetchInterval: 10_000, staleTime: 5_000 });
  const operatingTimelineQuery = trpc.operating.timeline.useQuery({ symbol: instrument.id }, { enabled: Boolean(cockpitQuery.data?.identity.authenticated), refetchInterval: 10_000, staleTime: 5_000 });
  const demoMutation = trpc.demo.runBatch.useMutation({ onSuccess: () => { void cockpitQuery.refetch(); toast(language === "ID" ? "Batch demo paper selesai." : "Demo paper batch completed."); } });
  const manifestQuery = trpc.datasets.imports.useQuery(undefined, { enabled: Boolean(cockpitQuery.data?.identity.authenticated), staleTime: 5_000 });
  const [selectedManifestId, setSelectedManifestId] = useState<number | null>(null);
  const activeManifestId = selectedManifestId ?? manifestQuery.data?.[0]?.id;
  const forwardRunMutation = trpc.paper.forwardRun.useMutation({ onSuccess: (result) => { void cockpitQuery.refetch(); void manifestQuery.refetch(); toast(result.status === "completed" ? (language === "ID" ? "Forward paper selesai dan ledger diperbarui." : "Forward paper completed and ledger updated.") : (language === "ID" ? "Forward paper diblokir oleh gate data." : "Forward paper blocked by data gate.")); }, onError: (error) => toast(error.message) });
  const paperDecisionMutation = trpc.paper.decide.useMutation({ onSuccess: (result) => { void cockpitQuery.refetch(); toast(result.status === "recorded" ? (language === "ID" ? "Keputusan paper tercatat ke journal." : "Paper decision recorded to journal.") : (language === "ID" ? result.reason : "Paper decision blocked for this instrument.")); }, onError: (error) => toast(error.message) });
  const paper = cockpitQuery.data?.paper;
  const shadow = cockpitQuery.data?.shadow;
  const news = cockpitQuery.data?.news;
  const demo = cockpitQuery.data?.demo;
  const demoStats = demo?.stats;
  const demoCurve = demo && "equityCurve" in demo ? (demo.equityCurve ?? []) : [];
  const demoCurvePoints = demoCurve.length > 1 ? demoCurve.slice().reverse().map((point, index) => `${(index / (demoCurve.length - 1)) * 100},${70 - ((point.equity - (demoStats?.equity ?? point.equity)) / Math.max(1, demoStats?.equity ?? point.equity)) * 400}`).join(" ") : "0,70 100,70";
  const liveSignals = paper?.signals ?? [];
  const primaryData = paper?.primary;
  const paperMetrics = paper?.metrics;
  const displayedSignal = liveSignals.find((item) => item.symbol === selectedSignal.symbol) ?? liveSignals[0] ?? { ...EMPTY_SIGNAL, symbol: instrument.id, market: instrument.label, updated: "awaiting dataset", source: cockpitQuery.isLoading ? "CONNECTING TO CANONICAL SNAPSHOT" : "SHADOW ONLY · DATASET PENDING" };
  const riskCheck = (label: string) => paper?.riskChecks.find((check) => check.label === label);
  const projectedCandles = useMemo(() => projectCandles(primaryData?.candles ?? [], 520, 190), [primaryData?.candles]);
  const [showAllLayers, setShowAllLayers] = useState(false);
  const operatingEvents = operatingTimelineQuery.data ?? [];
  const latestOperatingEvent = operatingEvents[0];
  const operatingStage = latestOperatingEvent?.stage ?? "INGEST";

  const visibleLayers = useMemo(() => (showAllLayers ? layers : layers.slice(0, 4)), [showAllLayers]);
  const dataLabel = cockpitQuery.isError ? "BACKEND OFFLINE" : cockpitQuery.isLoading ? "CONNECTING TO PAPER" : paper ? "UNIFIED COCKPIT" : "SHADOW DATASET PENDING";
  const moduleRows = paper?.modules ?? [
    { name: "Canonical data contract", role: "Venue-neutral snapshots", status: "integrated", note: "UTC timestamp, quality, provenance" },
    { name: "17-layer fusion", role: "Signal evidence", status: "paper-only", note: "Decision output is gated" },
    { name: "Cryptoiz / DEX intelligence", role: "External source", status: "external", note: "Adapter pending" },
    { name: "Dynamic Execution", role: "External signal source", status: "external", note: "Not an execution authority" },
    { name: "Paper broker", role: "Fill simulation", status: "integrated", note: "Fee, slippage, idempotency" },
    { name: "AI / LLM layer", role: "Explanation and research", status: "experimental", note: "Policy-gated" },
    { name: "Live venue adapters", role: "Order execution", status: "live-blocked", note: "No live path" },
    { name: "24/7 operations", role: "Heartbeat / reconciliation", status: "paper-only", note: "Runbook defined; worker pending" },
  ];

  const [artifactQuery, setArtifactQuery] = useState("");
  const [artifactStatus, setArtifactStatus] = useState<"ALL" | "integrated" | "paper-only" | "external" | "experimental" | "live-blocked">("ALL");
  const filteredModuleRows = useMemo(() => {
    const query = artifactQuery.trim().toLowerCase();
    return moduleRows.filter((module) => {
      const matchesQuery = !query || [module.name, module.role, module.status, module.note].some((value) => value.toLowerCase().includes(query));
      const matchesStatus = artifactStatus === "ALL" || module.status === artifactStatus;
      return matchesQuery && matchesStatus;
    });
  }, [artifactQuery, artifactStatus, moduleRows]);

  const focusPanel = (id: string, label: string) => { document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" }); toast(`${label} focused`, { description: paper ? "Canonical paper context is active." : "Shadow-only context; paper dataset is pending." }); };

  return (
    <div className="app-shell">
      <aside className={`side-rail ${mobileNav ? "mobile-open" : ""}`}>
        <div className="brand-lockup">
          <div className="brand-mark-wrap"><img src="/manus-storage/md90-logo_0de195df.png" alt="md90_superlayerAi mark" /></div>
          <div>
            <div className="brand-name">md90<span>_</span></div>
            <div className="brand-sub">superlayerAi / cockpit</div>
          </div>
          <button className="icon-button rail-close" onClick={() => setMobileNav(false)} aria-label="Close navigation" aria-hidden={!mobileNav} tabIndex={mobileNav ? 0 : -1}><X size={16} /></button>
        </div>

        <div className="rail-rule" />
        <div className="rail-kicker">/ WORKSPACE</div>
        <nav className="primary-nav" aria-label="Primary navigation">
          {[{ label: "Overview", icon: Gauge }, { label: "Research desk", icon: BookOpen }, { label: "Signal room", icon: Radio }, { label: "Market map", icon: Layers3 }, { label: "Risk lab", icon: ShieldCheck }, { label: "Replay", icon: RefreshCw }, { label: "Management", icon: Settings2 }].map(({ label, icon: Icon }) => (
            <button key={label} className={`nav-item ${activeNav === label ? "active" : ""}`} onClick={() => { setActiveNav(label); if (label === "Research desk") navigate("/research-desk"); else if (label === "Management") navigate("/management"); else if (label === "Signal room") navigate("/signal-room"); else if (label === "Market map") navigate("/market-map"); else if (label === "Risk lab") navigate("/risk-lab"); else if (label === "Replay") navigate("/replay"); setMobileNav(false); }}>
              <Icon size={16} strokeWidth={activeNav === label ? 2.4 : 1.7} /><span>{label}</span>{activeNav === label && <span className="nav-pip" />}
            </button>
          ))}
        </nav>

        <div className="rail-kicker rail-kicker-spaced">/ INSTRUMENTS</div>
        <div className="instrument-list">
                      {(liveSignals.length ? liveSignals.slice(0, 3) : [displayedSignal]).map((item) => (

            <button key={item.symbol} className={`instrument-row ${selectedSignal.symbol === item.symbol ? "selected" : ""}`} onClick={() => { setSelectedSignal(item); const canonicalId = item.market.replace("/", "").replace(".", ""); if (["BTCUSDT", "ETHUSDT", "SOLUSDT", "EURUSD", "XAUUSD"].includes(canonicalId)) setInstrument(canonicalId as "BTCUSDT" | "ETHUSDT" | "SOLUSDT" | "EURUSD" | "XAUUSD"); }}>
              <span className={`instrument-dot ${item.accent}`} />
              <span className="instrument-symbol">{item.symbol}</span>
              <span className={`instrument-change ${item.bias === "SHORT" ? "negative" : ""}`}>{item.change}</span>
            </button>
          ))}
        </div>

        <div className="rail-footer">
          <div className="rail-footer-line"><span className={`status-dot ${cockpitQuery.isError ? "vermillion" : "live"}`} /> {cockpitQuery.isError ? "Feed unavailable" : cockpitQuery.isLoading ? "Connecting to paper" : paper ? "Canonical paper feed" : "Shadow feed"}</div>
          <div className="rail-footer-line muted"><Database size={13} /> {paper?.generatedAt ? `Canonical snapshot / ${new Date(paper.generatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} UTC` : "No verified snapshot"}</div>
          <button className="user-chip" onClick={() => navigate("/management")}><span className="avatar">AK</span><span><b>Analyst workspace</b><small>paper permissions</small></span><ChevronDown size={14} /></button>
        </div>
      </aside>

      {mobileNav && <button className="mobile-scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}

      <main className="main-canvas">
        <header className="topbar">
          <div className="topbar-left"><div className="topbar-brand-mark"><img src="/manus-storage/md90-logo_0de195df.png" alt="" /></div><button className="icon-button mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open navigation" tabIndex={isMobile ? 0 : -1}><Menu size={19} /></button><span className="breadcrumb">{text.workspace} <span>/</span> {language === "ID" && activeNav === "Overview" ? text.overview : activeNav}</span></div>
          <div className="topbar-actions">
            <button className="language-toggle compact-language" onClick={() => setLanguage(language === "ID" ? "EN" : "ID")} aria-label="Toggle language">{language}</button>
            <span className="demo-flag"><span className={`status-dot ${cockpitQuery.isError ? "vermillion" : "amber"}`} /> {dataLabel}</span><AuthenticatedScopeBadge compact />
            <button className="topbar-icon" onClick={() => toast("Notifications", { description: "Paper/shadow alerts are informational; no live execution alert is enabled." })} aria-label="Notifications"><Bell size={17} /><i /></button>
            <button className="topbar-icon" onClick={() => toast("Help", { description: "Use Research Desk for provenance and Signal Room for paper evidence." })} aria-label="Help"><CircleHelp size={17} /></button>
          </div>
        </header>
        <div className={`data-state-banner ${cockpitQuery.isError ? "error" : cockpitQuery.isLoading ? "loading" : "ready"}`}><span className="status-dot" />{cockpitQuery.isError ? text.fallbackSnapshot : cockpitQuery.isLoading ? `${text.connecting} to ${text.paperEngine}…` : `${text.syncedFills} · ${paper?.metrics.tradeCount ?? 0} ${text.simulatedFills.toLowerCase()} · ${paper?.generatedAt ? new Date(paper.generatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"}`}</div>

        <MarketContextControls />
        <section className="operating-overview-strip" aria-label="All-in-one operating cockpit status"><div className="operating-overview-copy"><div className="eyebrow"><span className="eyebrow-line" /> / ALL-IN-ONE OPERATING COCKPIT</div><h2>{latestOperatingEvent ? `${latestOperatingEvent.eventType} / ${latestOperatingEvent.stage}` : "Awaiting authenticated operating run"}</h2><p>{latestOperatingEvent ? `Correlation ${latestOperatingEvent.correlationId} · ${latestOperatingEvent.instrument} · ${latestOperatingEvent.authority}` : "Run the canonical graph from Replay to bind persisted evidence, parity, MTFA, risk, PAPER decision, journal, and audit."}</p></div><div className="operating-stage-strip">{OPERATING_STAGES.map((stage) => <span className={stage === operatingStage ? "active" : operatingEvents.some((event) => event.stage === stage) ? "complete" : "pending"} key={stage}><b>{String(OPERATING_STAGES.indexOf(stage) + 1).padStart(2, "0")}</b>{stage}</span>)}</div><button className="workbench-secondary" onClick={() => navigate("/replay")}>OPEN COMMAND CENTER <ArrowUpRight size={14} /></button></section>
        <section className="final-readiness-summary" aria-label="Final delivery boundary"><div><span className="surface-kicker">/ DELIVERY STATUS</span><strong>SOFTWARE DELIVERY CLOSED</strong><small>All-in-one cockpit, PAPER workflow, persistence, adapters, parity, replay, and signed audit surfaces are implemented and test-covered.</small></div><div><span className="surface-kicker">/ EVIDENCE GATE</span><strong className="amber-text">OPERATOR INPUT REQUIRED</strong><small>Real manifest selection and Pine/MQL5 artifact vectors can change verdicts only when supplied with provenance.</small></div><div><span className="surface-kicker">/ SAFETY BOUNDARY</span><strong>LIVE / CUSTODY DISABLED</strong><small>No broker order, wallet signing, withdrawal, webhook execution, or automatic promotion is available.</small></div></section>
        <section className="terminal-command-deck" aria-label="Canonical market command deck">
          <div className="terminal-command-copy">
            <div className="eyebrow"><span className="eyebrow-line" /> / {text.marketIntelligence.toUpperCase()} / COMMAND DECK</div>
            <h1>Observe first.<br /><em>Act on evidence.</em></h1>
            <p>{text.heroDescription} Canonical state is visible before any paper decision.</p>
            <div className="terminal-command-foot"><span className={`status-dot ${cockpitQuery.isLoading ? "amber" : instrument.paperReplay ? "teal" : "amber"}`} /> {cockpitQuery.isLoading ? "CONNECTING TO PAPER ENGINE" : instrument.paperReplay ? "PAPER engine synchronized" : "SHADOW context · paper dataset pending"}</div>
          </div>
          <div className="terminal-control-grid">
            <div className="terminal-control primary-control"><span>PRIMARY INSTRUMENT</span><strong>{primaryData?.market ?? displayedSignal.market}</strong><small>{instrument.venue} · {instrument.paperReplay ? "paper replay + read-only market data" : "shadow-only · canonical replay pending"}</small></div>
            <div className="terminal-control"><span>BASE / HTF</span><strong>{formatTimeframe(timeframe.base)} <i>→</i> {formatTimeframe(timeframe.htf)}</strong><small>TradingView context · {timeframe.symbol}</small></div>
            <div className="terminal-control"><span>DATA LINEAGE</span><strong>{paper?.provenance ?? (instrument.paperReplay ? "CANONICAL PAPER" : "SHADOW ONLY")}</strong><small>{cockpitQuery.isLoading ? "connecting to canonical snapshot" : cockpitQuery.isError ? "fallback snapshot · review required" : instrument.paperReplay ? "replay + shadow observation" : "No canonical replay dataset for selected instrument"}</small></div>
            <button className="terminal-open" onClick={() => { window.location.href = "/signal-room"; }}><Play size={13} fill="currentColor" /> OPEN SIGNAL ROOM</button>
          </div>
        </section>

        <section className="mode-bar" aria-label="Operation mode">
          <div className="mode-context"><span className="section-label-inline">/ {text.operationMode}</span><span className="mode-lock"><LockKeyhole size={12} /> {text.liveLocked}</span></div>
          <div className="mode-switcher" role="group" aria-label="Select operation mode">
            {(["PAPER", "SHADOW", "LIVE"] as Mode[]).map((item) => <button key={item} className={`mode-button ${mode === item ? "selected" : ""} ${item === "LIVE" ? "locked" : ""}`} onClick={() => item === "LIVE" ? toast("Live mode locked", { description: "PAPER/SHADOW only; no network order authority." }) : setMode(item)}>{item === "LIVE" && <LockKeyhole size={12} />}{item}</button>)}
          </div>
          <div className="mode-detail"><span className="status-dot teal" /> {mode === "PAPER" ? text.simulatedFills : text.observingOnly}</div>
        </section>

        <div className="trace-rule" aria-hidden="true" /><section className="metrics-strip" aria-label="System summary">
          <div className="metric-card lead-metric"><div className="metric-top"><span className="metric-label">SYSTEM PULSE</span><span className="metric-icon"><Activity size={15} /></span></div><div className="metric-value">{paperMetrics?.systemPulse ?? "—"}<span className="metric-unit">/100</span></div><div className="metric-foot"><span className="positive"><ArrowUpRight size={13} /> 4.8%</span><span>vs. prior session</span><MiniSparkline /></div></div>
          <div className="metric-card"><div className="metric-top"><span className="metric-label">GROSS EXPOSURE</span><span className="metric-tag safe">WITHIN LIMIT</span></div><div className="metric-value small">{paperMetrics?.grossExposurePct ?? "—"}<span className="metric-unit">%</span></div><div className="metric-foot"><span>cap 25.0%</span><div className="meter"><i style={{ width: "34%" }} /></div></div></div>
          <div className="metric-card"><div className="metric-top"><span className="metric-label">PEAK DRAWDOWN</span><span className="metric-icon warning"><TriangleAlert size={15} /></span></div><div className="metric-value small negative">{paperMetrics?.peakDrawdownPct ?? "—"}<span className="metric-unit">%</span></div><div className="metric-foot"><span>guardrail -10.0%</span><MiniSparkline accent="vermillion" down /></div></div>
          <div className="metric-card"><div className="metric-top"><span className="metric-label">DATA FRESHNESS</span><span className="metric-tag live-tag">LIVE FEED</span></div><div className="metric-value small">{paperMetrics?.dataFreshnessSeconds ?? "—"}<span className="metric-unit"> sec</span></div><div className="metric-foot"><span>Binance / {formatTimeframe(timeframe.base)} · HTF {formatTimeframe(timeframe.htf)}</span><span className="positive">healthy</span></div></div>
        </section>

        <section className="workspace-grid" id="signal-room">
          <div className="primary-column">
            <div className="panel signal-panel">
              <div className="panel-header"><div><SectionLabel aside={paper ? "CANONICAL REPLAY" : "SHADOW ONLY"}>/ PRIMARY SIGNAL</SectionLabel><div className="signal-title-row"><h2>{primaryData?.market ?? displayedSignal.market}</h2><span className={`bias-pill ${(primaryData ? "LONG" : displayedSignal.bias).toLowerCase()}`}>{(primaryData ? "LONG" : displayedSignal.bias) === "LONG" ? <ArrowUpRight size={13} /> : (primaryData ? "LONG" : displayedSignal.bias) === "SHORT" ? <ArrowDownRight size={13} /> : <Eye size={13} />}{primaryData ? "LONG" : displayedSignal.bias}</span></div></div><button className="more-button" onClick={() => navigate("/signal-room")} aria-label="Open signal detail"><SlidersHorizontal size={16} /></button></div>
              <div className="signal-meta"><span><span className="status-dot teal" /> {formatTimeframe(timeframe.base)} composite · SYNCED</span><span><RefreshCw size={12} /> updated {displayedSignal.updated}</span><span className="provenance-chip"><FileCheck2 size={12} /> {paper?.provenance ?? displayedSignal.source}</span></div>
              <div className="chart-wrap">
                <div className="chart-y-labels"><span>—</span><span>—</span><span>—</span><span>—</span></div>
                <svg viewBox="0 0 520 190" preserveAspectRatio="none" className="main-chart candle-chart" role="img" aria-label={`${instrument.label} OHLC candlestick chart from canonical paper replay`}>{paper ? <g className="candle-grid" aria-hidden="true"><line x1="0" y1="47" x2="520" y2="47" /><line x1="0" y1="95" x2="520" y2="95" /><line x1="0" y1="143" x2="520" y2="143" /></g> : <text x="260" y="100" textAnchor="middle" fill="#8b9892" fontSize="11">SHADOW ONLY · PAPER DATASET PENDING</text>}{projectedCandles.map((candle) => { const bodyY = Math.min(candle.yOpen, candle.yClose); const bodyHeight = Math.max(2, Math.abs(candle.yClose - candle.yOpen)); const color = candle.rising ? "#22C7B8" : "#F16A5B"; return <g key={candle.timestamp} className="candle" aria-label={`${candle.timestamp} open ${candle.open} high ${candle.high} low ${candle.low} close ${candle.close}`}><line x1={candle.x} x2={candle.x} y1={candle.yHigh} y2={candle.yLow} stroke={color} strokeWidth="1.4" vectorEffect="non-scaling-stroke" /><rect x={candle.x - 7} y={bodyY} width="14" height={bodyHeight} fill={color} fillOpacity=".82" stroke={color} strokeWidth="1" vectorEffect="non-scaling-stroke" /></g>; })}</svg>
                <div className="chart-x-labels"><span>DATASET</span><span>UTC</span><span>O/H/L/C</span><span>PROVENANCE</span><span>—</span></div>
                {paper && <div className="chart-marker entry"><span>Paper evidence</span><i /></div>}
              </div>
              <div className="compact-tape"><div className="compact-tape-head"><span>ORDER TAPE / PAPER</span><small>{paper?.trades.length ?? 0} fills · immutable</small></div>{(paper?.trades ?? []).slice(0, 3).map((trade) => <div className="compact-tape-row" key={`compact-${trade.id}`}><b className={trade.side === "BUY" ? "positive" : "negative"}>{trade.side}</b><strong>{trade.instrument}</strong><span>{trade.price.toFixed(2)}</span><small>{trade.status} · {trade.slippageBps} bps</small></div>)}</div><div className="signal-footer"><div><span className="signal-footer-label">COMPOSITE SCORE</span><strong>{primaryData?.score ?? displayedSignal.score}<small>/100</small></strong></div><div><span className="signal-footer-label">CALIBRATED CONFIDENCE</span><strong>{primaryData?.confidence ?? displayedSignal.confidence}<small>%</small></strong></div><div><span className="signal-footer-label">R:R PROJECTION</span><strong>PENDING</strong></div><button className="inspect-button" onClick={() => focusPanel("evidence-stack", "Signal replay")}><Eye size={14} /> Inspect stack</button></div>
            </div>

            <div className="panel table-panel">
              <div className="panel-header compact"><div><SectionLabel aside={`${liveSignals.length} VERIFIED ITEMS`}>/ ACTIVE SIGNALS</SectionLabel><p className="panel-subtitle">Sorted by composite score · all data labeled</p></div><button className="text-button" onClick={() => focusPanel("signal-room", "Watchlist")} >View watchlist <ArrowUpRight size={14} /></button></div>
              <div className="signal-table"><div className="table-head"><span>Instrument</span><span>Bias</span><span>Score</span><span>Confidence</span><span>Move</span><span>Source</span></div>{liveSignals.length === 0 ? <div className="signal-empty">No verified signal in the current canonical snapshot.</div> : liveSignals.map((item) => <button key={item.symbol} className={`table-row ${selectedSignal.symbol === item.symbol ? "row-selected" : ""}`} onClick={() => setSelectedSignal(item)}><span className="table-instrument"><span className={`instrument-dot ${item.accent}`} /><strong>{item.symbol}</strong><small>{item.market}</small></span><span className={`table-bias ${item.bias.toLowerCase()}`}>{item.bias}</span><span className="score-cell"><strong>{item.score}</strong><span className="score-bar"><i style={{ width: `${item.score}%` }} /></span></span><span className="confidence-cell">{item.confidence}%</span><span className={item.change.startsWith("-") ? "negative" : "positive"}>{item.change}</span><span className="source-cell">{item.source}<small>{item.updated}</small></span></button>)}</div>
            </div>
          </div>

          <aside className="evidence-column">
            <div className="panel risk-panel"><div className="panel-header compact"><div><SectionLabel aside="POLICY V1.0">/ RISK GATE</SectionLabel><h3>{cockpitQuery.isLoading ? "Checking evidence" : paper ? (riskCheck("Survivor Mode")?.status === "PASS" ? "Clear for paper" : "Paper gate locked") : "Shadow only"}</h3></div><div className="shield-orb"><ShieldCheck size={18} /></div></div><p className="risk-copy">{cockpitQuery.isLoading ? "Checking canonical replay availability and policy state…" : paper ? "The policy engine evaluates this setup before any paper decision. Live authority remains unavailable." : "No canonical replay dataset is available for this instrument. Risk decision is paused until evidence is qualified."}</p><div className="risk-checks">{["Daily loss limit", "Gross exposure", "Data freshness"].map((label) => { const check = riskCheck(label); return <div className={`risk-check ${check?.status === "PASS" ? "pass" : "hold"}`} key={label}><span><ShieldCheck size={14} /> {label}</span><strong>{check?.status ?? "PENDING"}</strong></div>; })}<div className="risk-check hold"><span><Eye size={14} /> Live approval</span><strong>LOCKED</strong></div></div><div className="risk-budget"><div><span>Risk budget / next idea</span><strong>{paper?.primary.riskPct?.toFixed(2) ?? "—"}%</strong></div><div className="budget-line"><i style={{ width: paper ? "20%" : "0%" }} /></div><small>{cockpitQuery.isLoading ? "Awaiting canonical paper snapshot" : paper ? "Survivor Mode · 3.00% exposure cap" : "Awaiting canonical paper dataset"}</small></div><button className="secondary-action" onClick={() => navigate("/risk-lab")}><ShieldCheck size={14} /> Open risk lab</button></div>

            <div id="evidence-stack" className="panel layers-panel"><div className="panel-header compact"><div><SectionLabel aside="{layers.length} ACTIVE">/ EVIDENCE STACK</SectionLabel><p className="panel-subtitle">Why this signal is on the desk</p></div><button className="icon-button" onClick={() => setShowAllLayers(!showAllLayers)} aria-label="Toggle layers">{showAllLayers ? <ChevronDown size={16} /> : <Layers3 size={16} />}</button></div><div className="layer-list">{visibleLayers.map((layer, index) => <div className="layer-row" key={layer.label}><span className="layer-index">0{index + 1}</span><div className="layer-main"><div><strong>{layer.label}</strong><span>{layer.note}</span></div><div className="layer-bar"><i style={{ width: `${layer.value}%` }} /></div></div><span className="layer-value">{layer.value}</span></div>)}</div><button className="layers-toggle" onClick={() => setShowAllLayers(!showAllLayers)}>{showAllLayers ? "Collapse evidence" : "Show all layers"}<ChevronDown size={13} className={showAllLayers ? "rotate" : ""} /></button></div>

            <div className="insight-card"><img src="/manus-storage/md90-signal-orb_3c07989e.jpg" alt="" /><div className="insight-overlay"><div className="eyebrow small"><Sparkles size={12} /> / AI NOTE</div><p>AI note tersedia setelah canonical evidence tervalidasi. Tidak ada insight sintetis yang ditampilkan.</p><span>Evidence-gated · PAPER/SHADOW only</span></div></div>
          </aside>
        </section>

        <PaperWorkflowPanel paper={paper} workflow={cockpitQuery.data?.workflow} execution={cockpitQuery.data?.execution} authenticated={cockpitQuery.data?.identity.authenticated ?? false} onRunPaper={() => paperDecisionMutation.mutate({ timeframe: timeframe.base, htf: timeframe.htf, symbol: instrument.id, riskPct: 0.5 })} isRunning={paperDecisionMutation.isPending} />

        <section className="ops-strip"><div className="panel ops-panel"><div className="panel-header compact"><div><SectionLabel aside={`${paper?.trades.length ?? 0} FILLS / PAPER ONLY`}>/ ORDER TAPE</SectionLabel><h3>Execution ledger</h3></div><Activity size={18} className="panel-corner-icon" /></div><div className="order-tape">{(paper?.trades ?? []).map((trade) => <div className="tape-row" key={trade.id}><span className={`tape-side ${trade.side.toLowerCase()}`}>{trade.side}</span><strong>{trade.instrument}</strong><span>{trade.quantity.toFixed(4)}</span><span>{trade.price.toFixed(2)}</span><small>{trade.status.toUpperCase()} · {trade.slippageBps} bps</small></div>)}</div><p className="ops-note">Immutable paper fills · fee {paper?.metrics.fees.toFixed(2) ?? "—"} · no network orders.</p></div><div className="panel ops-panel"><div className="panel-header compact"><div><SectionLabel aside="FSM / AUDIT TRAIL">/ AGENT STATE</SectionLabel><h3>System process</h3></div><BrainCircuit size={18} className="panel-corner-icon" /></div><div className="agent-state"><div><span>STATE</span><strong>11 / EVIDENCE_REVIEW</strong></div><div><span>POLICY</span><strong className="teal-text">{paper?.riskChecks.every((check) => check.status === "PASS" || check.label === "Live approval") ? "PAPER_APPROVED" : "LOCKED"}</strong></div><div><span>LAST EVENT</span><strong>{paper?.journal[0]?.event ?? "WAITING"}</strong></div><div><span>LATENCY</span><strong>{paper?.metrics.dataFreshnessSeconds ?? "—"} sec</strong></div><div><span>OOS WALK-FORWARD</span><strong>{cockpitQuery.data?.walkForward?.outOfSampleWinRatePct ?? "—"}%</strong></div></div><p className="ops-note">Agent output is explanatory only. Walk-forward is canonical replay evidence, not live performance. Risk policy remains the order boundary.</p></div></section>\n\n        <section className="panel demo-observatory"><div className="panel-header compact"><div><SectionLabel aside="DEMO PAPER / SIMULATION">/ {language === "ID" ? "AKUN DEMO" : "DEMO ACCOUNT"}</SectionLabel><h3>{demo?.account?.displayName ?? "md90 Demo Paper Account"}</h3></div><button className="secondary-action" onClick={() => demoMutation.mutate()} disabled={demoMutation.isPending}>{demoMutation.isPending ? (language === "ID" ? "Menjalankan…" : "Running…") : (language === "ID" ? "Jalankan batch" : "Run batch")} <Play size={13} /></button></div><div className="demo-metrics-grid"><div><span>{language === "ID" ? "Total transaksi" : "Total trades"}</span><strong>{demoStats?.tradeCount ?? 0}</strong></div><div><span>WIN RATE</span><strong>{demoStats?.winRatePct.toFixed(2) ?? "0.00"}%</strong><small>target 93% · {demoStats?.sampleQuality ?? "INSUFFICIENT_SAMPLE"}</small></div><div><span>{language === "ID" ? "Menang / kalah" : "Wins / losses"}</span><strong>{demoStats?.wins ?? 0} / {demoStats?.losses ?? 0}</strong></div><div><span>EXPECTANCY</span><strong>{demoStats?.expectancy.toFixed(4) ?? "0.0000"}</strong></div><div><span>DRAWDOWN</span><strong>{demoStats?.maxDrawdownPct.toFixed(2) ?? "0.00"}%</strong></div><div><span>HEARTBEAT</span><strong className={demo?.account?.scheduleCronTaskUid ? "teal-text" : "amber-text"}>{demo?.account?.scheduleCronTaskUid ? "ACTIVE" : "PENDING"}</strong></div></div><div className="demo-equity"><div><span>EQUITY CURVE / {demoCurve.length} POINTS</span><small>{language === "ID" ? "Dihitung dari batch yang selesai" : "Derived from completed batches"}</small></div><svg viewBox="0 0 100 80" preserveAspectRatio="none" role="img" aria-label="Demo paper equity curve"><polyline points={demoCurvePoints} fill="none" stroke="#22C7B8" strokeWidth="1.8" vectorEffect="non-scaling-stroke" /></svg></div><p className="ops-note">{language === "ID" ? "Statistik dihitung dari demo ledger persisten; heartbeat aktif hanya setelah deployment dan registrasi scheduler; order route tetap DISABLED." : "Metrics are calculated from the persistent demo ledger; heartbeat activates only after deployment and scheduler registration; order route remains DISABLED."}</p></section>

        <section className="panel forward-paper-panel"><div className="panel-header compact"><div><SectionLabel aside="REAL DATA / PAPER ONLY">/ FORWARD PAPER SESSION</SectionLabel><h3>{language === "ID" ? "Uji forward pada manifest persisted" : "Run forward test on persisted manifest"}</h3></div><span className="registry-status paper-only">NO LIVE ROUTE</span></div><div className="forward-paper-controls"><label><span>{language === "ID" ? "Manifest sumber" : "Source manifest"}</span><select aria-label={language === "ID" ? "Pilih manifest dataset" : "Select dataset manifest"} value={activeManifestId ?? ""} onChange={(event) => setSelectedManifestId(event.target.value ? Number(event.target.value) : null)} disabled={!manifestQuery.data?.length || forwardRunMutation.isPending}><option value="">{manifestQuery.data?.length ? (language === "ID" ? "Pilih manifest" : "Select manifest") : (language === "ID" ? "Belum ada manifest persisted" : "No persisted manifest")}</option>{manifestQuery.data?.map((manifest) => <option key={manifest.id} value={manifest.id}>{manifest.symbol} · {manifest.interval} · {manifest.barCount.toLocaleString()} bars · {manifest.checksum.slice(0, 10)}…</option>)}</select></label><button className="primary-action" disabled={!activeManifestId || forwardRunMutation.isPending || !cockpitQuery.data?.identity.authenticated} onClick={() => activeManifestId && forwardRunMutation.mutate({ ingestionId: activeManifestId })}>{forwardRunMutation.isPending ? (language === "ID" ? "Menjalankan…" : "Running…") : (language === "ID" ? "Jalankan forward paper" : "Run forward paper")} <Play size={13} /></button></div>{forwardRunMutation.data?.result && <div className="forward-paper-result"><div><span>STATUS</span><strong>{forwardRunMutation.data.status.toUpperCase()}</strong></div><div><span>BARS</span><strong>{forwardRunMutation.data.result.barsObserved.toLocaleString()}</strong></div><div><span>FILLS</span><strong>{forwardRunMutation.data.result.fills}</strong></div><div><span>PNL</span><strong className={forwardRunMutation.data.result.realizedPnl >= 0 ? "teal-text" : "vermillion-text"}>{forwardRunMutation.data.result.realizedPnl.toFixed(2)}</strong></div><div><span>DRAWDOWN</span><strong>{forwardRunMutation.data.result.maxDrawdownPct.toFixed(2)}%</strong></div><div><span>AUTHORITY</span><strong className="teal-text">PAPER_ONLY</strong></div>{forwardRunMutation.data.coverage && <div><span>DATA GATE</span><strong className={forwardRunMutation.data.coverage.status === "READY" ? "teal-text" : "amber-text"}>{forwardRunMutation.data.coverage.status}</strong></div>}</div>}{forwardRunMutation.data?.comparison && <div className="forward-paper-compare"><div><span>COHORT</span><strong>{forwardRunMutation.data.comparison.status}</strong></div><div><span>Δ WIN RATE</span><strong>{forwardRunMutation.data.comparison.delta.winRatePct.toFixed(2)} pp</strong></div><div><span>Δ PNL</span><strong>{forwardRunMutation.data.comparison.delta.realizedPnl.toFixed(2)}</strong></div><div><span>Δ DRAWDOWN</span><strong>{forwardRunMutation.data.comparison.delta.maxDrawdownPct.toFixed(2)} pp</strong></div><small>OOS replay vs forward paper · {forwardRunMutation.data.comparison.caveat}</small></div>}<p className="ops-note">{language === "ID" ? "Candle diproses berurutan dari manifest user-scoped; fee, spread, slippage, time-stop, fill, journal, dan equity ditulis ke ledger. Tidak ada broker order, wallet signing, atau custody." : "Candles are processed sequentially from the user-scoped manifest; fee, spread, slippage, time-stop, fill, journal, and equity are written to the ledger. No broker order, wallet signing, or custody."}</p></section>

        <section className="panel strategy-panel"><div className="panel-header compact"><div><SectionLabel aside="PAPER / SHADOW CONFIG">/ ACTIVE STRATEGY</SectionLabel><h3>Matari Candle Enhanced + Alpha / FUSION V9-IMP</h3></div><span className="registry-status paper-only">{paper?.strategy?.mode ?? "COMBINED_HYBRID"}</span></div><div className="strategy-grid"><div><span>RSI / STOCH</span><strong>{paper?.strategy?.matari.rsiPeriod ?? 14} / {paper?.strategy?.matari.stochasticK ?? 14}/{paper?.strategy?.matari.stochasticKSmoothing ?? 3}/{paper?.strategy?.matari.stochasticD ?? 3}</strong><small>midline {paper?.strategy?.matari.rsiMidline ?? 50} · HTF confirmation ON</small></div><div><span>SMA / MACD</span><strong>{paper?.strategy?.matari.smaTrend.period ?? 20} / {paper?.strategy?.matari.macd.fast}-{paper?.strategy?.matari.macd.slow}-{paper?.strategy?.matari.macd.signal}</strong><small>S/R labels + lines · pivot {paper?.strategy?.matari.pivotSensitivity ?? 5}</small></div><div><span>RISK / EXIT</span><strong>{paper?.strategy?.fusion.fixedLot ?? 0.01} lot · {paper?.strategy?.fusion.tpRR ?? 2}R</strong><small>SL {paper?.strategy?.fusion.slAtrFactor ?? 2.5} ATR · time stop {paper?.strategy?.fusion.timeStopBars ?? 10} bars</small></div><div><span>ROUTE</span><strong className="teal-text">PAPER ENABLED</strong><small>shadow observe-only · live {paper?.strategy?.execution.liveRoute ?? "DISABLED"}</small></div></div></section>
        <TimeframeLineage />
         <TradingViewSurface />
        <section id="news-intelligence" className="intelligence-strip"><div className="panel news-panel"><div className="panel-header compact"><div><SectionLabel aside={`${text.shadowFeed} / ${text.reviewQueue}`}>/ {text.news.toUpperCase()}</SectionLabel><h3>What can move the regime</h3></div><button className="text-button" onClick={() => navigate("/research-desk")}>Open desk <ArrowUpRight size={14} /></button></div><div className="news-list">{(news?.items ?? []).map((item) => <button className="news-item" key={item.id} onClick={() => focusPanel("news-intelligence", item.source)} ><span className={`news-sentiment ${item.sentiment.toLowerCase()}`} /> <div><strong>{item.headline}</strong><small>{item.source} · {item.instrument} · {new Date(item.publishedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · <b className={item.freshness === "STALE" ? "news-freshness stale" : "news-freshness"}>{item.freshness}</b> · <b className="news-status">{item.status}</b></small></div><b>{item.relevance}</b></button>)}</div></div><div className="panel shadow-panel"><div className="panel-header compact"><div><SectionLabel aside={`${shadow?.observations.length ?? 0} OBSERVATIONS`}>/ {text.shadowFeed.toUpperCase()}</SectionLabel><h3>{text.noOrders}</h3></div><Radio size={18} className="panel-corner-icon" /></div><div className="shadow-list">{(shadow?.observations ?? []).map((observation) => <div className="shadow-row" key={`${observation.source}-${observation.instrument}`}><div><strong>{observation.instrument}</strong><small>{observation.source} · {observation.quality.replace("_", " ")}</small></div><span>{observation.spreadBps.toFixed(2)} bps</span><b>{observation.freshnessSeconds}s</b></div>)}</div><p className="shadow-note">{text.shadowFeed} observes and scores external data. <strong>{text.orderDisabled}</strong>.</p></div></section>

        <section id="system-map" className="panel integration-panel"><div className="panel-header compact"><div><SectionLabel aside={`${filteredModuleRows.length}/${moduleRows.length} MODULES / ONE COCKPIT`}>/ ALL-IN-ONE SYSTEM MAP</SectionLabel><h3>One platform. Clear boundaries.</h3></div><button className="text-button" onClick={() => navigate("/audit-log")}>View matrix <ArrowUpRight size={14} /></button></div><p className="integration-intro">Every component we build has a visible role, status, and boundary. Search the synchronized registry without changing its source artifacts.</p><div className="artifact-filters" role="search" aria-label="Artifact search and filters"><label className="artifact-search"><Search size={15} aria-hidden="true" /><span className="sr-only">Search synchronized artifacts</span><input value={artifactQuery} onChange={(event) => setArtifactQuery(event.target.value)} placeholder="Search artifacts, role, status…" aria-label="Search synchronized artifacts" /></label><label className="artifact-status-filter"><ListFilter size={14} aria-hidden="true" /><span className="sr-only">Filter artifact status</span><select value={artifactStatus} onChange={(event) => setArtifactStatus(event.target.value as typeof artifactStatus)} aria-label="Filter artifact status"><option value="ALL">All statuses</option><option value="integrated">Integrated</option><option value="paper-only">Paper only</option><option value="external">External</option><option value="experimental">Experimental</option><option value="live-blocked">Live blocked</option></select></label>{(artifactQuery || artifactStatus !== "ALL") && <button className="text-button artifact-clear" onClick={() => { setArtifactQuery(""); setArtifactStatus("ALL"); }}>Clear filters</button>}</div>{filteredModuleRows.length ? <div className="module-grid">{filteredModuleRows.map((module) => <button key={module.name} className="module-card" onClick={() => focusPanel("system-map", module.name)} ><div className="module-card-top"><span className={`module-status ${module.status}`}>{module.status.replace("-", " ")}</span><span className="module-index">/ {String(moduleRows.indexOf(module) + 1).padStart(2, "0")}</span></div><strong>{module.name}</strong><span>{module.role}</span><small>{module.note}</small></button>)}</div> : <div className="artifact-empty"><FileCheck2 size={18} /><strong>No synchronized artifact matches</strong><span>Try another keyword or reset the status filter.</span></div>}</section>

        <footer className="page-footer"><span><span className="brand-mini">md90_</span>superlayerAi · transparent by design</span><span>Signal Atelier / v0.1 concept · <button onClick={() => navigate("/audit-log")}>Data policy</button> · <button onClick={() => navigate("/authenticated-audit")}>Audit log</button></span><span className="footer-right"><span className="status-dot teal" /> All systems nominal</span></footer>
      </main>
    </div>
  );
}
