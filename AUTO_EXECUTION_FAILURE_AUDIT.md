# Auto-Execution Failure-Mode Audit

## Scope

Materi pengguna mengidentifikasi dua kegagalan utama pada bot auto-execution: **entry yang terlalu generik** dan **gerbang eksternal yang terlalu kaku**. Audit md90 memperluasnya menjadi failure modes yang dapat diuji tanpa mengubah sistem menjadi agresif atau membuka live order.

| Failure mode | Dampak | Prinsip perbaikan md90 | Boundary |
|---|---|---|---|
| Three-EMA/entry terlalu generik | Overtrading pada pasar sideways atau regime yang berubah | Konfirmasi regime dan volatility; sinyal lemah menjadi `WATCH`, bukan order | Paper/shadow |
| Filter score eksternal terlalu tinggi | Tidak ada entry meskipun kondisi valid; sistem tampak “mati” | Threshold menjadi konfigurasi bounded dengan floor/ceiling dan audit perubahan | Paper only; shadow tidak order |
| Threshold terlalu rendah | Entry berkualitas buruk dan false positive meningkat | Threshold tidak boleh turun di bawah minimum; perlu evidence count dan confidence | Fail-closed |
| Volatilitas tidak dipertimbangkan | SL/TP statis tidak proporsional terhadap noise pasar | ATR/volatility bucket mengubah risk distance dan size secara deterministic | Paper/shadow |
| Latensi dan quote drift | Harga berubah antara keputusan dan fill | Toleransi slippage berbasis bps dengan hard cap; jika terlampaui, reject/reprice paper fill | Paper only |
| Partial fill diabaikan | Exposure aktual berbeda dari intent | Fill ledger menyimpan quantity aktual dan idempotent client order id | Paper only |
| Scaling-out didahulukan dari entry validity | Kompleksitas TP tidak berguna atau membentuk state palsu | State machine: validate entry → open paper position → manage scale-out | Paper only |
| Duplicate/retry execution | Posisi ganda ketika worker/HTTP retry | Batch/order idempotency dan unique keys | All non-live paths |
| Stale or future data | Keputusan memakai informasi tidak valid | Freshness classifier, timestamp UTC, reject future/stale inputs | Fail-closed |
| Risk budget drift | Size membesar hanya karena score tinggi | Position size diturunkan dari risk budget dan volatility; cap exposure/drawdown | Paper only |
| Single-signal rigidity | Bot gagal merespons konflik antar layer | Evidence stack menghasilkan `LONG`, `SHORT`, `WATCH`, atau `BLOCKED`; konflik tidak dipaksa menjadi trade | Paper/shadow |
| Live credential leakage | Demo/test dapat menyentuh venue | Tidak ada live credential atau network order path; live route `DISABLED` | Live-blocked |

## Design decision

“Bot tidak kaku” tidak berarti melonggarkan semua filter. Artinya sistem dapat membedakan **valid no-trade**, **watch**, **paper entry**, dan **blocked** berdasarkan konteks yang tercatat. Threshold, volatility bucket, latency, dan slippage tetap memiliki batas keras, provenance, dan alasan keputusan yang dapat direplay.

## Acceptance criteria

A change is accepted only when the bot can handle both sides of the failure described in the source: it must not remain permanently silent because one external score is too strict, and it must not become permissive enough to trade through stale data, excessive spread, insufficient evidence, or a breached risk budget. All new behavior remains PAPER/SHADOW until separate validation gates are satisfied.
