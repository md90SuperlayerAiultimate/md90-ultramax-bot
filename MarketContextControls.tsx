import { INSTRUMENTS } from "@shared/instruments";
import { BASE_TIMEFRAMES, HTF_TIMEFRAMES, formatTimeframe, type BaseTimeframe, type HtfTimeframe } from "@shared/timeframe";
import { useTimeframe } from "@/contexts/TimeframeContext";

export default function MarketContextControls() {
  const { timeframe, instrument, setInstrument, setBase, setHtf } = useTimeframe();
  return <section className="market-context-controls" aria-label="Global market context controls">
    <div className="context-control-heading"><span>/ GLOBAL CONTEXT</span><strong>MTFA control plane</strong><small>One selection updates paper, shadow, risk, and TradingView read-only state.</small></div>
    <label><span>INSTRUMENT</span><select value={instrument.id} onChange={(event) => setInstrument(event.target.value as typeof instrument.id)}>{INSTRUMENTS.map((item) => <option key={item.id} value={item.id}>{item.label} · {item.assetClass}</option>)}</select></label>
    <label><span>BASE TF</span><select value={timeframe.base} onChange={(event) => setBase(event.target.value as BaseTimeframe)}>{BASE_TIMEFRAMES.map((value) => <option key={value} value={value}>{formatTimeframe(value)}</option>)}</select></label>
    <label><span>HTF / MTFA</span><select value={timeframe.htf} onChange={(event) => setHtf(event.target.value as HtfTimeframe)}>{HTF_TIMEFRAMES.map((value) => <option key={value} value={value}>{formatTimeframe(value)}</option>)}</select></label>
    <div className="context-control-state"><b>SYNCED</b><small>{instrument.tradingView} · {timeframe.source} · UTC</small></div>
  </section>;
}
