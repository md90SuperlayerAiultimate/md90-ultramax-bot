import { useEffect, useMemo, useState } from "react";
import { BASE_TIMEFRAMES, HTF_TIMEFRAMES, formatTimeframe, timeframeToTradingViewInterval, type CanonicalTimeframe } from "@shared/timeframe";
import { INSTRUMENTS } from "@shared/instruments";
import { useTimeframe } from "@/contexts/TimeframeContext";

const intervals = BASE_TIMEFRAMES;
type ChartInterval = (typeof intervals)[number];

export type TradingViewStatus = "CONNECTING" | "CONNECTED" | "UNAVAILABLE";

export function transitionTradingViewStatus(event: "selection-changed" | "load" | "error"): TradingViewStatus {
  if (event === "load") return "CONNECTED";
  if (event === "error") return "UNAVAILABLE";
  return "CONNECTING";
}

export function buildTradingViewUrl(symbol: string, interval: string) {
  const tvInterval = timeframeToTradingViewInterval(interval as CanonicalTimeframe["base"] | CanonicalTimeframe["htf"]);
  return `https://www.tradingview.com/widgetembed/?frameElementId=md90_tradingview&symbol=${encodeURIComponent(symbol)}&interval=${tvInterval}&hidesidetoolbar=1&hidetoptoolbar=1&symboledit=0&saveimage=0&toolbarbg=111615&studies=%5B%5D&theme=dark&style=1&timezone=Etc%2FUTC&withdateranges=1&hideideas=1&hidelegend=0&hidevolume=0&locale=en`;
}

export function buildMtfaRows(base: ChartInterval, htf: (typeof HTF_TIMEFRAMES)[number]) {
  return intervals.map((interval) => ({
    interval,
    tvInterval: timeframeToTradingViewInterval(interval),
    role: interval === base ? "BASE" : htf !== "same" && interval === htf ? "HTF" : "CONTEXT",
    selected: interval === base || (htf !== "same" && interval === htf),
  }));
}

export default function TradingViewSurface({ timeframe: suppliedTimeframe }: { timeframe?: CanonicalTimeframe }) {
  const global = useTimeframe();
  const timeframe = suppliedTimeframe ?? global.timeframe;
  const [status, setStatus] = useState<TradingViewStatus>("CONNECTING");
  const src = useMemo(() => buildTradingViewUrl(timeframe.symbol, timeframe.base), [timeframe.symbol, timeframe.base]);
  const timeframeRows = useMemo(() => buildMtfaRows(timeframe.base, timeframe.htf), [timeframe.base, timeframe.htf]);

  useEffect(() => setStatus(transitionTradingViewStatus("selection-changed")), [timeframe.symbol, timeframe.base]);

  return <div className="tv-surface">
    <div className="tv-surface-head">
      <div><span>TRADINGVIEW / MTFA RESEARCH ONLY</span><strong>{timeframe.symbol}</strong><small>global context · {formatTimeframe(timeframe.base)} base · {formatTimeframe(timeframe.htf)} HTF · UTC · no broker order authority</small></div>
      <div className="tv-controls">
        <span className={`tv-status ${status.toLowerCase()}`}><i /> {status}</span>
        <label>Symbol<select aria-label="TradingView instrument" value={global.instrument.id} onChange={(event) => global.setInstrument(event.target.value as typeof global.instrument.id)}>{INSTRUMENTS.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
        <label>TF<select aria-label="TradingView base timeframe" value={timeframe.base} onChange={(event) => global.setBase(event.target.value as typeof timeframe.base)}>{intervals.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>HTF<select aria-label="TradingView higher timeframe" value={timeframe.htf} onChange={(event) => global.setHtf(event.target.value as typeof timeframe.htf)}>{HTF_TIMEFRAMES.map((item) => <option key={item} value={item}>{item.toUpperCase()}</option>)}</select></label>
      </div>
    </div>
    <div className="tv-mtfa-strip" aria-label="Multi-timeframe analysis status">
      <div className="tv-mtfa-label"><span>MTFA CONTROL PLANE</span><strong>ONE SYMBOL · NINE CONTEXTS</strong><small>Changing base or HTF updates the canonical paper/shadow context.</small></div>
      {timeframeRows.map((row) => <div className={`tv-timeframe-card ${row.selected ? "selected" : ""}`} key={row.interval}>
        <span>{row.role}</span><strong>{formatTimeframe(row.interval)}</strong><small>TV {row.tvInterval} · {row.selected ? "SYNCED" : "AVAILABLE"}</small>
      </div>)}
    </div>
    <div className="tv-frame"><iframe title={`TradingView read-only chart for ${timeframe.symbol}`} src={src} loading="lazy" referrerPolicy="origin" onLoad={() => setStatus(transitionTradingViewStatus("load"))} onError={() => setStatus(transitionTradingViewStatus("error"))} /></div>
    <div className="tv-surface-foot"><span className="tv-sync-state">MTFA SYNCED · {formatTimeframe(timeframe.base)} / {formatTimeframe(timeframe.htf)}</span><span>{timeframe.source} · UTC · canonical signals remain md90 / SHADOW</span><span>READ-ONLY · LIVE ROUTE DISABLED</span></div>
  </div>;
}
