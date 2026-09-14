# Per-chat effort selector

## Goal

Expose only verified, selectable reasoning effort levels in DeepSeek Harness without implying unsupported capability for other OmniRoute models.

## Scope

- Add the provider-advertised levels to `cx/gpt-5.6-sol`, `antigravity/gemini-3.7-flash-tiered`, `cgpt-web/gpt-5.6-sol-pro`, and `openrouter/z-ai/glm-5.2:free`.
- Send the selected level through the OpenAI-compatible `reasoning_effort` field.
- Leave every other model unchanged until its provider publishes a tier list; `gweb/gemini-3.6-flash` explicitly does not support effort controls.

## Configuration

The `omniroute-vm1205` model profile declares `reasoningEfforts` with each provider's exact levels and enables OpenAI reasoning-effort compatibility. The Harness UI then presents the selector per chat when that model is selected.

## Verification

- Parse the updated YAML and assert the exact model capability profile.
- Restart the Harness and verify its local HTTP endpoint.
- Confirm the protected Harness UI displays all five choices and accepts a per-chat selection.

## Rollback

Restore `/home/dsh/.dsh/settings.yaml.bak-20260915T0154-effort-selector` on VM105, then restart `deepseek-harness`.
