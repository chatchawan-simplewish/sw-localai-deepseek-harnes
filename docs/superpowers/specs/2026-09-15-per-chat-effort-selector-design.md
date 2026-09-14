# Per-chat effort selector

## Goal

Expose only verified, selectable reasoning effort levels in DeepSeek Harness without implying unsupported capability for other OmniRoute models.

## Scope

- Add the provider-advertised levels to `cx/gpt-5.6-sol`, `antigravity/gemini-3.7-flash-tiered`, `cgpt-web/gpt-5.6-sol-pro`, and `openrouter/z-ai/glm-5.2:free`.
- Add `Off`, `Low`, `Medium`, and `XHigh` to `llama-cpp/qwen3.8-27b`; its server-side Qwen template supports exactly those native levels.
- Add `Off`, `High`, and `XHigh` to `zw/glm-5.2`.
- Send the selected level through the OpenAI-compatible `reasoning_effort` field, or through `chat_template_kwargs.reasoning_effort` for local Qwen.
- Leave every other model unchanged until its provider publishes a tier list; `gweb/gemini-3.6-flash` explicitly does not support effort controls.

## Configuration

The `omniroute-vm1205` model profile declares `reasoningEfforts` with each provider's exact levels and enables the matching compatibility format. YAML's `off` key is quoted so it remains the literal selector value instead of parsing as a boolean. The Harness UI then presents the selector per chat when that model is selected.

## Verification

- Parse the updated YAML and assert the exact model capability profile, including Qwen's `off,low,medium,xhigh` map and native chat-template argument.
- Restart the Harness and verify its local HTTP endpoint.
- Confirm the protected Harness UI displays Qwen's `Default`, `Off`, `Low`, `Medium`, and `XHigh` choices, then restore the original per-chat model selection.

## Rollback

Restore the newest timestamped `/home/dsh/.dsh/settings.yaml.bak-*-qwen-effort-levels` or `*-quote-off-keys` backup on VM105, then restart `deepseek-harness`.
