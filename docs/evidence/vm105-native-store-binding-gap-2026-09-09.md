# Retained source and effective-store gap

20260909 051023 Asia/Bangkok. DeepSeek Harness: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Read-only assessment by `/root/store_binding_assessment`; no live reads, acquisition, profile access or modification.

The retained base-composition receipt contains the complete base patch: `credentials` selects `@deepseek-ai/dsh-credentials-local` without config, and no authorization literal is present. This proves the base row only. The candidate blueprint leaves that row untouched. Neither proves the effective composed profile or mounted services.

`C:/Users/chatc/.codex/tmp-native-oauth-entries.json` retains the complete 248-line authorization implementation. The assessor reconstructed its bytes and reproduced SHA256 `d86547a2f450ff7f58f421f5e2a91eab6abc5ac3dc2ae90cd3785d15547002a3`. The implementation requires credentials injection and a credential update during the attempt plus configured status afterward. The separate offline synthetic checker in `vm105-native-authorization-contract-2026-09-09.md` is now independently accepted against these retained bytes; it does not invoke native OAuth or establish actual injection.

`C:/Users/chatc/.codex/tmp-native-surface-boot.json` retains full profile boot source, with bundle, profile, home and overlay ordering. `tmp-native-surface-headless.json` retains app-boot composition semantics. Base-plus-profile inspection alone cannot exclude later home/overlay overrides.

`vm105-v1-source-revalidation-2026-09-09.json` retains the credentials-local implementation digest `1688f17801d5809abace4ef6228b771625a0153c043d7d4dba21b398ec4056eb`, but not its bytes. No implementation bytes were found in the inspected local native captures; this is a bounded search result, not a whole-machine absence claim.

Before claiming real store binding, locate existing retained credentials-local implementation bytes and reproduce that pin. If unavailable, prepare a distinct exact missing-source scope for independent review; do not replay prior readers. Then establish final selected-home configuration, service mounting and ambient authentication exclusions through a separately reviewed isolated runtime scope. Opaque `/home/dsh/.dsh` remains unread and unchanged.

The bridge's `ctx.credentials` presence check cannot establish a filesystem path, and authorization.begin has no store-path argument. Actual effective store, service injection, native credentials and cutover remain NOT PROVEN. No route or evidence count advances.
