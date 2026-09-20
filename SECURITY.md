# Security Policy

## Scope

Repository ini berisi cockpit riset dan paper-trading. Jalur live broker order, wallet signing, custody, withdrawal, dan external execution tetap disabled.

## Jangan kirim secret

Jangan pernah memasukkan API key, API secret, private key, wallet seed, OAuth secret, database URL, atau token provider ke source, issue, pull request, screenshot, ZIP, atau log. Gunakan environment secret resmi pada hosting/provider bila integrasi read-only diperlukan.

## Melaporkan vulnerability

Laporkan vulnerability secara private melalui GitHub Security Advisories bila tersedia. Jika fitur tersebut belum tersedia pada paket repository, jangan mempublikasikan credential atau proof-of-concept sensitif; hubungi owner repository melalui kanal privat yang terverifikasi.

## Quality gates

Perubahan wajib melewati CI test/typecheck/build dan secret scan. Perubahan dependency harus melewati Dependency Review pada pull request. Branch protection belum dapat diaktifkan pada private repository GitHub Free; status ini didokumentasikan dan tidak boleh dianggap sebagai kontrol aktif.
