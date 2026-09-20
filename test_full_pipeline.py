"""
MD90 v4 — Integration Tests
Tests semua komponen tanpa MT5 atau exchange connection.
"""
import sys, os, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from md90_brain.types import MarketData, SignalDirection
from md90_brain.constants import LAYER_WEIGHTS, LAYER_NAMES, TOTAL_LAYERS

# ── Generate synthetic MarketData ─────────────────────────────────────
def make_market_data(trend="bull", n=300) -> MarketData:
    import random, math
    random.seed(42)
    price = 50000.0
    opens, highs, lows, closes, volumes = [], [], [], [], []
    for i in range(n):
        drift = 10 if trend=="bull" else (-10 if trend=="bear" else 0)
        o = price
        c = o + drift + random.uniform(-200, 220)
        h = max(o,c) + random.uniform(0, 100)
        l = min(o,c) - random.uniform(0, 100)
        v = random.uniform(800, 2000)
        opens.append(o); highs.append(h); lows.append(l)
        closes.append(c); volumes.append(v)
        price = c

    p = closes[-1]
    ema8  = sum(closes[-8:]) /8
    ema21 = sum(closes[-21:])/21
    ema50 = sum(closes[-50:])/50

    return MarketData(
        symbol="BTC/USDT", timeframe="15m",
        closes=closes, highs=highs, lows=lows,
        opens=opens, volumes=volumes, current_price=p,
        atr=abs(p)*0.005, atr_avg=abs(p)*0.004, atr_ratio=1.25,
        ema8=ema8, ema21=ema21, ema50=ema50, ema200_d=p*0.95,
        adx=32.0, di_plus=28.0, di_minus=18.0,
        rsi=55.0, macd_main=0.002, macd_signal=0.001, macd_hist=0.001,
        stoch_k=60.0, stoch_d=55.0,
        obv=1000000.0, obv_prev=990000.0,
        mfi=55.0, volume_ratio=1.3, buy_pressure=55.0,
        volume_spike=False, vwap=p*0.999,
        bb_upper=p*1.01, bb_mid=p, bb_lower=p*0.99, bb_width_pct=2.0,
        mtf_ema21={"5m":p*0.998,"15m":p*0.999,"1h":p*0.995,"4h":p*0.99,"1d":p*0.98},
        mtf_close={"5m":p,"15m":p,"1h":p*1.001,"4h":p*1.002,"1d":p*1.005},
        session_active=True,
    )


class TestLayerSystem(unittest.TestCase):
    def test_weights_sum_100(self):
        self.assertAlmostEqual(sum(LAYER_WEIGHTS)*100, 100.0, places=0)

    def test_17_layers(self):
        self.assertEqual(TOTAL_LAYERS, 17)
        self.assertEqual(len(LAYER_NAMES), 17)
        self.assertEqual(len(LAYER_WEIGHTS), 17)

    def test_layer_names_correct(self):
        expected_first = ["SNR","EMA","RSI","Stochastic","OrderBlock"]
        for i,n in enumerate(expected_first):
            self.assertEqual(LAYER_NAMES[i], n)


class TestSignalEngine(unittest.TestCase):
    def test_analyze_returns_17(self):
        from md90_brain.signal_engine import SignalEngine
        eng = SignalEngine()
        md = make_market_data("bull")
        sigs = eng.analyze(md)
        self.assertEqual(len(sigs), 17)

    def test_directions_valid(self):
        from md90_brain.signal_engine import SignalEngine
        eng = SignalEngine()
        md = make_market_data("bull")
        sigs = eng.analyze(md)
        valid_dirs = {int(SignalDirection.BUY), int(SignalDirection.SELL),
                      int(SignalDirection.NEUTRAL)}
        for s in sigs:
            self.assertIn(s.direction, valid_dirs)

    def test_strengths_bounded(self):
        from md90_brain.signal_engine import SignalEngine
        eng = SignalEngine()
        md = make_market_data("bull")
        sigs = eng.analyze(md)
        for s in sigs:
            self.assertGreaterEqual(s.strength, 0.0)
            self.assertLessEqual(s.strength, 1.0)


class TestFusionScoring(unittest.TestCase):
    def test_full_analyze(self):
        from md90_brain.signal_engine import SignalEngine
        from md90_brain.fusion import full_analyze
        eng = SignalEngine()
        md = make_market_data("bull")
        layers = eng.analyze(md)
        sig = full_analyze(layers, md.current_price, md.atr,
                           md.atr_ratio, md.volume_spike)
        self.assertIn(sig.execution_status, ["ALL-IN","WAITING","ABORT"])
        self.assertGreaterEqual(sig.confidence, 0.0)
        self.assertLessEqual(sig.confidence, 100.0)
        self.assertEqual(len(sig.take_profit), 6)
        self.assertEqual(len(sig.risk_reward), 6)

    def test_gate_structure(self):
        from md90_brain.signal_engine import SignalEngine
        from md90_brain.fusion import full_analyze
        eng = SignalEngine()
        md = make_market_data("bear")
        layers = eng.analyze(md)
        sig = full_analyze(layers, md.current_price, md.atr,
                           md.atr_ratio, md.volume_spike)
        # Verify gate attributes exist
        for gate in ["gate1_passed","gate2_passed","gate3_passed",
                     "gate4_passed","gate5_passed","all_gates_passed"]:
            self.assertIsInstance(getattr(sig, gate), bool)

    def test_lot_multiplier_range(self):
        from md90_brain.signal_engine import SignalEngine
        from md90_brain.fusion import full_analyze
        eng = SignalEngine()
        md = make_market_data("bull")
        layers = eng.analyze(md)
        sig = full_analyze(layers, md.current_price, md.atr,
                           md.atr_ratio, md.volume_spike)
        self.assertIn(sig.lot_multiplier, [0.5, 1.0, 1.5, 2.0])


class TestRegimeEngine(unittest.TestCase):
    def test_8_regimes(self):
        from md90_brain.regime_engine import RegimeEngine, MarketRegime
        eng = RegimeEngine()
        md = make_market_data("bull")
        state = eng.analyze(md.closes, md.highs, md.lows,
                            md.atr, md.adx, md.di_plus, md.di_minus, md.volume_ratio)
        valid = {r for r in MarketRegime}
        self.assertIn(state.regime, valid)
        self.assertGreaterEqual(state.confidence, 0)
        self.assertLessEqual(state.confidence, 100)

    def test_trending_up_detected(self):
        from md90_brain.regime_engine import RegimeEngine, MarketRegime
        eng = RegimeEngine()
        md = make_market_data("bull")
        state = eng.analyze(md.closes, md.highs, md.lows,
                            md.atr, 35.0, 30.0, 15.0, 1.5)
        self.assertEqual(state.regime, MarketRegime.TRENDING_UP)


class TestSessionManager(unittest.TestCase):
    def test_returns_session_state(self):
        from md90_brain.session_manager import SessionManager, TradingSession
        mgr = SessionManager()
        from datetime import datetime, timezone
        dt = datetime(2024, 3, 15, 14, 30, tzinfo=timezone.utc)  # Friday 14:30 UTC
        state = mgr.detect(dt)
        # 14:30 UTC = London-NY overlap (13:00-16:00)
        self.assertEqual(state.session, TradingSession.OVERLAP_LN)
        self.assertTrue(state.is_active)
        self.assertEqual(state.risk_mult, 2.0)

    def test_weekend_no_trading(self):
        from md90_brain.session_manager import SessionManager, TradingSession
        from datetime import datetime, timezone
        mgr = SessionManager()
        dt = datetime(2024, 3, 16, 12, 0, tzinfo=timezone.utc)  # Saturday
        state = mgr.detect(dt)
        self.assertEqual(state.session, TradingSession.WEEKEND)
        self.assertFalse(state.is_active)


class TestDynamicRisk(unittest.TestCase):
    def test_normal_risk(self):
        from md90_brain.risk_calculator import DynamicRiskCalculator
        from md90_brain.session_manager import SessionManager
        from md90_brain.regime_engine import RegimeEngine
        from datetime import datetime, timezone
        calc = DynamicRiskCalculator()
        sm = SessionManager()
        re = RegimeEngine()
        md = make_market_data("bull")
        sess   = sm.detect(datetime(2024,3,15,14,30,tzinfo=timezone.utc))
        regime = re.analyze(md.closes,md.highs,md.lows,md.atr,35.,30.,15.,1.5)
        rs = calc.calculate(sess, regime, equity=10000, balance=10000)
        self.assertTrue(rs.trading_allowed)
        self.assertGreater(rs.final_risk_pct, 0)

    def test_halt_on_big_dd(self):
        from md90_brain.risk_calculator import DynamicRiskCalculator, MAX_DRAWDOWN_PCT
        from md90_brain.session_manager import SessionManager
        from md90_brain.regime_engine import RegimeEngine
        from datetime import datetime, timezone
        calc = DynamicRiskCalculator()
        calc._equity_peak = 10000
        calc._current_equity = 10000 * (1 - MAX_DRAWDOWN_PCT/100 - 0.01)
        sm = SessionManager()
        re = RegimeEngine()
        md = make_market_data("bull")
        sess   = sm.detect(datetime(2024,3,15,14,30,tzinfo=timezone.utc))
        regime = re.analyze(md.closes,md.highs,md.lows,md.atr,35.,30.,15.,1.5)
        rs = calc.calculate(sess, regime, equity=calc._current_equity, balance=10000)
        self.assertFalse(rs.trading_allowed)


class TestQuadForce(unittest.TestCase):
    def test_returns_quad_signal(self):
        from md90_brain.quad_force import QuadForceEngine, QuadSignal
        eng = QuadForceEngine()
        md = make_market_data("bull")
        sig = eng.analyze(md)
        self.assertIsInstance(sig, QuadSignal)
        self.assertIn(sig.direction, [-1, 0, 1])
        self.assertGreaterEqual(sig.confidence, 0)
        self.assertLessEqual(sig.confidence, 100)

    def test_bear_market_sells(self):
        from md90_brain.quad_force import QuadForceEngine
        from md90_brain.types import SignalDirection
        eng = QuadForceEngine()
        md = make_market_data("bear")
        md.ema8=49000; md.ema21=50000; md.ema50=51000
        md.adx=35; md.di_minus=30; md.di_plus=10; md.rsi=35
        sig = eng.analyze(md)
        self.assertLessEqual(sig.buy_score, sig.sell_score)


class TestMLAdaptive(unittest.TestCase):
    def test_record_and_retrain(self):
        from ml import AdaptiveWeights
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        ml = AdaptiveWeights(path)
        init_weights = ml.get_weights()
        self.assertEqual(len(init_weights), 17)
        self.assertAlmostEqual(sum(init_weights), 1.0, places=2)
        # Record 20 trades to trigger retrain
        for i in range(20):
            dirs = [1]*10 + [-1]*7
            ml.record(dirs, 1, 10.0 if i%2==0 else -5.0)
        final_weights = ml.get_weights()
        self.assertEqual(len(final_weights), 17)
        os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
