# Core source capture limit

The independently pre-reviewed reader `ab7793a940ed9338536bfda5fedb7a9ab96adc6b77385f8fc6f257a300c2553f` ran once at2026-09-08T21:29:14 UTC (2026-09-09 04:29:14 Asia/Bangkok). SSH exited0 and the response reported PUBLIC_CORE_SOURCE_PASS. This attempt is consumed.

The parent selected a12000-token command-output budget; the18582-token response was truncated in transit to the model. The exact received partial output is retained in `vm105-core-source-partial-2026-09-09.txt`. It is not valid complete JSON and does not retain the whole source. This is an evidence-retention defect, not proof of remote source failure. No automatic retry was performed.

Intact metadata identifies declared runtime entry `lib/index.js`,60378UTF-8 bytes,1828lines, remote SHA256 `1729cdbf8ee40b17c8839e06bf96491490548559e11ef7e411271e0754e751c5`. Full local source hash reproduction is NOT PROVEN. The retained tail reports `os_unshare=true` and `os_clone_newnet=true`; no namespace was created.

Independent assessment of the remaining lifecycle excerpts is pending. Any further acquisition needs an explicit changed capture implementation and pre-review; it must not replay this spent reader unchanged. The usable pilot, profiles, services, authentication and provider routes were not accessed by this source read.

## Reviewed capture correction

V2 reader `e5aee9bc9d553a0c864679062904ee8c981f588fc8037676f4a859b1e6b5675d` changed only local receipt transport to bounded zlib/base64. Independent pre-review accepted it at04:39:46. One new source acquisition ran at04:40:07 UTC+07, SSH0; V2 is now consumed too. Remote public-file scope remained unchanged.

Parent decoded and verified the complete74224-byte receipt, SHA256 `f84e506f495c28bca8409d34d9c5e5201258f1839e83819a7bac98371e94930f`, and saved those exact bytes as `vm105-native-core-source-2026-09-09.json`. A fresh file digest matched. The complete60378-byte source reconstructed SHA256 `1729cdbf8ee40b17c8839e06bf96491490548559e11ef7e411271e0754e751c5`, matching the earlier remote metadata. The original partial artifact remains historical; full-source retention is now verified. Native lifecycle assessment is separate.
