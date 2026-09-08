# VM105 Typhoon OCR wire readiness — 2026-09-09

Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Bounded public-source audit; no provider request, credential/profile access, image processing or inference. Installed-source budget: 03/03 files consumed.

**Result: the OCR chat-completions/image wire shape is established from public source, and the installed Harness adapter has an image-forwarding path. Full route compatibility, authenticated access and OCR quality remain NOT PROVEN. No route is released.**

## Official contract, date-scoped

The [official OCR documentation](https://docs.opentyphoon.ai/en/ocr/) identifies `typhoon-ocr` as OCR 1.5 and the recommended model; its helper returns Markdown and does not require the legacy task-type choice. This does not prove account access or runtime behavior.

The [official helper source](https://raw.githubusercontent.com/scb-10x/typhoon-ocr/refs/heads/master/packages/typhoon_ocr/typhoon_ocr/ocr_utils.py), freshly captured at `2026-09-08T18:09:24.357888+00:00`, sends user text plus a PNG data URL (613–619) through OpenAI chat completions (660,691–709), with base `https://api.opentyphoon.ai/v1`, model `typhoon-ocr`, `max_tokens=16384`, repetition penalty 1.1, temperature 0.1 and top-p 0.6 for v1.5. It does not request streaming; v1.5 returns message content directly (710–713). Images are resized/encoded, and PDF pages rendered, before this request (568–606). The derived endpoint is `/v1/chat/completions`; PDFs are not sent as raw PDF bodies in this helper path.

This is a mutable master-branch capture, not an immutable commit claim. Older excerpts have different line numbers; this document uses the retained fresh source and hash below. No blocked GitHub API commit URL was retried or bypassed. No source was installed or executed.

The [general API reference](https://docs.opentyphoon.ai/en/api-reference/) documents the POST endpoint, SSE streaming, and optional top-p/repetition-penalty fields. Its examples use text models; it is useful compatibility evidence but is not an executed OCR-specific test. Its generic token-limit text differs from the OCR helper, so OCR capacity must not be inferred from that generic limit. Helper sampling choices are not mandatory acceptance requirements merely because the helper uses them.

## Installed Harness compatibility and gaps

| Boundary | Source-supported result | Remaining limitation |
| --- | --- | --- |
| Custom route | Adapter 709–712 and 932–943 supports `api: openai-completions`, `baseURL`, credential reference, explicit models, modality metadata and headers. | Candidate fields are not effective profile configuration. No provider identity, key or route was created. |
| Image admission | Adapter 651,862,918–924,1720–1723 requires image modality and the durable attachment service. Its unknown-model default is text only. | An explicitly image-capable model declaration and mounted attachment path must be established; a custom ID alone is insufficient. |
| Image conversion | Adapter 1072–1121 and 1182–1237 obtains request-image bytes and emits pi-ai base64 image blocks. Pi-ai wire module 802–831 maps these to `image_url` data URLs. | This is code-path evidence, not an executed upload/normalization test. Adapter 1083–1086 also inserts attachment-handle text. Image offloading/size policies and OCR preprocessing parity remain unproven. No general PDF-to-OCR equivalence is claimed. |
| Transport | Wire module 128–139,479–540 selects the configured base URL, invokes chat completions, and forwards image-bearing messages. | `stream: true` is forced at518. General API documentation supports SSE, while the OCR helper uses nonstreaming. This difference alone is not incompatibility. OCR-specific streaming and usage-chunk behavior remain untested; stream options include usage by default (525–526). |
| Output bounds | Adapter model `maxTokens` metadata and request `maxTokens`/temperature exist; wire 531–540 selects the output-token field. `compat.maxTokensField` is configurable (adapter370,889). | A candidate should explicitly select `max_tokens` rather than trust URL heuristics. Effective call limits/defaults and context capacity are not verified. |
| Extra sampling fields | Complete adapter schema932–964, profileOptions1538–1549 and call1738–1745 expose no top-p, repetition-penalty or arbitrary body/onPayload binding. Wire module has an internal `onPayload` hook at130 but Harness does not supply it here. | Exact helper parameter parity is not expressible through this examined route surface. This is a technical gap, not proof that omitted fields are mandatory for every successful OCR request; vendor-supported behavior must resolve it. |
| Conversation/tools | Adapter carries its Harness conversation; wire 543–558 can add tools and tool choice. | A normal coding-agent request is not automatically a dedicated OCR request. Required prompt, history/tool restrictions, response handling and OCR fidelity need a bounded design and acceptance test. |

The existing streamed image route is a source-supported candidate. Its exact OCR contract remains pending isolated credentials, effective image/attachment configuration and a separately authorized bounded synthetic acceptance test. Prefer this existing path; differences from helper defaults alone do not justify new architecture. Only if a real requirement demands exact helper parity should unsupported sampling fields/preprocessing trigger a separately reviewed implementation decision. Neither an adapter patch nor a replacement package was built. No API-key copy, port change, automatic routing or model fallback is proposed.

## Inspection and retained provenance

Independent review: `candidate_smoke_review` accepted document SHA256 `A885471442F46B4065EB98E46A549399429A4BC7150E7A8D1E9D90AA29A69313` before this annotation on2026-09-09 Asia/Bangkok. It recomputed all four retained source hashes and checked the cited wire/adapter paths and scoped conclusions. Transport exit0 remains author-reported wrapper evidence; source captures do not independently retain that exit. No runtime or route acceptance follows from this review.

The unchanged `Inspection` definitions from `scripts/inspect-vm105-pnpm-package.py` were hash-checked to `fcddc77c890b289e28c609fa30b3b41f6c060a73c5c4ea3ab69b468a130df424`. Each remote read used held nofollow descriptors, root ownership/non-writable ancestry, ACL/capability checks, stable metadata/path identity and double SHA256 reads. All three source files reported link count2. Each SSH wrapper required exit0 with the existing approved key, BatchMode, IdentitiesOnly, StrictHostKeyChecking, ConnectTimeout10 and `/usr/bin/python3.12 -I -` at the assigned VM105 endpoint. No installed JavaScript ran.

The adapter canonical path/hash came from `vm105-v1-source-revalidation-2026-09-09.json` and matched freshly before use. Its explicit import at10 names pi-ai `api/openai-completions.lazy`; the previously retained, locally hash-verified pi-ai manifest export `./api/*` → `./dist/api/*.js` determines file2. File2 explicitly imports file3. Canonical paths were read directly: this lane did not independently revalidate package symlink mappings or all imported helper implementations. No directory crawl or fourth installed file was consumed.

Full public sources are retained in these local captures; hashes can be reproduced from each UTF-8 `source` string:

1. `C:/Users/chatc/.codex/tmp-typhoon-ocr-adapter.json`; VM UTC `2026-09-08T18:07:24.586431+00:00`.
   - `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai/lib/index.js`
   - SHA256 `e183a9cdde703b47485410bd68d247c8becdb277c390f0f91c6dd28718d350e2`.
2. `C:/Users/chatc/.codex/tmp-typhoon-ocr-lazy.json`; VM UTC `2026-09-08T18:07:56.240702+00:00`.
   - `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.lazy.js`
   - SHA256 `a3d37d272ed600ddae2a9b05884e1c11c65487c1d8aa30d0b19ba571ffc7ea76`.
3. `C:/Users/chatc/.codex/tmp-typhoon-ocr-wire.json`; VM-reported UTC in capture.
   - `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js`
   - SHA256 `0d50250fe2931e66e2078279a397814202e1ecddee58faf4b8bc04c278da177a`.
4. Official public-source HTTP200 capture `C:/Users/chatc/.codex/tmp-typhoon-ocr-official.json`, source URL and retrieval timestamp retained.
   - SHA256 `6d741f1ea69c1fa625298a7f6d50e027cc73e3ee321c89b5fd76cdf41147ebdc`.

No credentials, environment, profile content, live logs, installed provider calls, images, browser actions, package installation, firewall writes, GPU load or hardware changes occurred. Existing blocked route packet and other owners' files are unchanged. Parent independent review and runtime acceptance remain separate.
