# Rencana 100 peningkatan Web Terminal MD90

Dokumen ini adalah backlog prioritas, bukan klaim fitur sudah selesai. Preview login, authenticated E2E, branch protection, serta VPS memerlukan akses dan bukti runtime yang tidak tersedia dari inspeksi kode saja. Live order tetap diblokir.

## E2E, identitas, bukti (1–10)
1. Jalankan preview E2E dalam sesi login resmi.
2. Catat correlation ID yang benar-benar dihasilkan.
3. Simpan commit SHA dan waktu UTC pada laporan E2E.
4. Uji login/logout dan kedaluwarsa sesi.
5. Uji semua mutasi tanpa autentikasi harus ditolak.
6. Uji isolasi data antar pengguna.
7. Uji alur snapshot → workflow → paper → persistence → reconciliation.
8. Uji jalur fail-closed dan alasan blokirnya.
9. Uji idempotensi retry agar tidak menggandakan record.
10. Simpan log E2E yang sudah disanitasi.

## CI dan tata kelola (11–20)
11. Jadikan CI check wajib setelah nama check tervalidasi.
12. Wajibkan review independen untuk perubahan sensitif.
13. Wajibkan penyelesaian seluruh percakapan review.
14. Larang force-push pada branch terlindungi.
15. Larang penghapusan branch default.
16. Tambahkan CODEOWNERS untuk auth, risk, dan deployment.
17. Jalankan Python lint/typecheck di CI.
18. Jalankan frontend typecheck, unit test, dan build.
19. Tambahkan dependency dan secret scanning.
20. Publikasikan laporan status CI per commit.

## Reconciliation dan ekspor (21–30)
21. Filter rekonsiliasi berdasarkan tanggal UTC.
22. Filter berdasarkan instrumen canonical.
23. Filter berdasarkan state exception.
24. Filter berdasarkan kategori exception.
25. Filter berdasarkan correlation ID.
26. Ekspor event trace terfilter ke JSON.
27. Ekspor event trace yang sama ke CSV.
28. Sertakan event/correlation/causation ID dan provenance.
29. Validasi rentang tanggal dan batas ukuran ekspor.
30. Uji kesetaraan isi ekspor JSON dan CSV.

## Monte Carlo dan statistik (31–40)
31. Tegaskan simulasi Monte Carlo hanya untuk riset/backtest.
32. Jelaskan null hypothesis dan metode resampling.
33. Tambahkan block bootstrap untuk serial dependence.
34. Cantumkan seed, jumlah sampel, dan checksum dataset.
35. Masukkan komisi, spread, slippage, latency, dan partial fills.
36. Uji sensitivitas skenario biaya.
37. Laporkan tail loss dan drawdown duration.
38. Audit look-ahead dan survivorship bias.
39. Pisahkan train, validation, dan test secara kronologis.
40. Koreksi multiple testing untuk banyak eksperimen.

## Tuning yang dibatasi (41–50)
41. Hasil tuning hanya proposal, bukan perubahan parameter otomatis.
42. Tuning hanya memakai train split.
43. Evaluasi pada out-of-sample yang tidak disentuh.
44. Simpan config/code/data hash setiap percobaan.
45. Batasi rentang parameter secara eksplisit.
46. Tambahkan walk-forward windows yang deterministik.
47. Bandingkan dengan baseline tetap dan no-trade baseline.
48. Penalti kompleksitas dan turnover.
49. Terapkan minimum sample size dan tampilkan ketidakpastian.
50. Simpan diff, reviewer, approval, dan rollback untuk proposal.

## Data belajar historis (51–60)
51. Gunakan hanya data yang diizinkan dan berprovenance.
52. Deduplicate record histori.
53. Keluarkan fill yang belum direkonsiliasi dari label hasil.
54. Pisahkan PAPER, SHADOW, DEMO, dan LIVE secara tegas.
55. Catat alasan record dimasukkan/dikeluarkan dari dataset.
56. Hindari leakage antara feature dan label masa depan.
57. Ukur kalibrasi per instrumen, regime, dan periode.
58. Pantau distribution drift dan hentikan rekomendasi bila menyimpang.
59. Version dataset, features, model, dan laporan.
60. Model tidak boleh mengubah risk limit atau execution authority.

## Artefak dan provenance (61–70)
61. Buat katalog SHA-256 metadata untuk file dan referensi.
62. Inventaris ZIP dari central directory tanpa ekstrak otomatis.
63. Label video/biner sebagai metadata-only kecuali parser ditinjau.
64. Catat sumber, lisensi, tanggal, checksum, dan status review.
65. Jangan perlakukan isi ZIP sebagai instruksi executable.
66. Batasi ukuran dan jumlah anggota arsip serta lindungi path traversal.
67. Scan kemungkinan credential sebelum artefak dipakai.
68. Tautkan setiap referensi ke sumber/checksum asal.
69. Pisahkan fakta terverifikasi, hipotesis, klaim pemasaran, dan unknown.
70. Uji stabilitas schema keluaran JSON/CSV katalog.

## Web terminal dan UI (71–80)
71. Pertahankan bind localhost sebagai default.
72. Hilangkan arbitrary shell dari surface yang dapat diakses internet.
73. Gunakan command allowlist, bukan shell bebas.
74. Tambahkan authz, CSRF, rate-limit, dan session expiry untuk aksi operator.
75. Audit setiap sesi terminal dan disconnect.
76. Tempelkan label PAPER/SHADOW/LIVE-BLOCKED di setiap aksi.
77. Tampilkan freshness/stale/disconnect pada chart dan data.
78. Tegaskan TradingView hanya chart/embed read-only.
79. Uji aksesibilitas keyboard dan pembaca layar.
80. Uji loading, error, empty, dan responsive desktop/mobile.

## Risiko dan operasi (81–90)
81. Pertahankan live order boundary fail-closed.
82. Simpan secret di secret manager, bukan frontend/log/repo.
83. Terapkan least-privilege untuk kredensial masa depan.
84. Uji position/order/loss/drawdown caps secara independen.
85. Uji kill switch pada sandbox dan audit tindakan operator.
86. Rekonsiliasi order/fill/balance/position sebelum promosi.
87. Halt pada selisih rekonsiliasi yang tidak dijelaskan.
88. Gunakan retry terbatas, backoff, idempotency, circuit breaker.
89. Pantau freshness, DB, queue lag, dan scheduler heartbeat.
90. Uji restore backup dan dokumentasikan retention/RPO/RTO.

## Deploy, rilis, pemeliharaan (91–100)
91. Jangan klaim deploy VPS tanpa health-check runtime yang berhasil.
92. Gunakan container non-root dan privilege minimal.
93. Pin dependencies dan buat image yang reproducible.
94. Redaksi secret dari log dan workflow CI.
95. Deploy staging dan jalankan smoke test sebelum production.
96. Dokumentasikan dan uji rollback non-production.
97. Gunakan structured logs dengan correlation ID.
98. Uji alert untuk outage, stale feed, risk block, dan reconciliation.
99. Dokumentasikan owner layanan, incident response, dan eskalasi.
100. Publikasikan live-readiness evidence review; checklist bukan otorisasi trading.

## Batas bukti

Kode repository yang diperiksa menunjukkan correlation/event lineage dan ekspor audit JSON/CSV dengan filter correlation/date pada Evidence Command Center; Monte Carlo/bootstrap/walk-forward juga sudah ada sebagai alat validasi. Hal tersebut tidak membuktikan preview E2E terbaru, deployment VPS, atau kesiapan live. Export/filter pada halaman reconciliation sendiri tetap perlu diverifikasi dan dilengkapi bila belum tersedia.
