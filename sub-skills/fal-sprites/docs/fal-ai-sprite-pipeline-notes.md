# fal.ai Sprite Pipeline — Notes & Learnings

## Migration Path

Tried three approaches for multi-frame sprite animation with character consistency:

1. **Local ComfyUI** — SDXL + IP-Adapter + OpenPose ControlNet on Apple Silicon. Failed: 8GB M1 Air can't run all three models simultaneously.
2. **RunComfy Cloud** — Cloud-hosted ComfyUI with serverless API. Failed: workflow setup (installing nodes, downloading models, Cloud Save, creating deployments) must be done manually in the browser. Not programmable via Claude Code.
3. **fal.ai** — API-driven model marketplace. Works: fully programmable, no infrastructure to manage.

## What Works

- fal.ai API via `fal_client` Python library — simple `subscribe()` pattern handles submission + polling
- IP-Adapter alone (character reference) — works well with large reference images
- ControlNet Union (pose mode) alone — works
- Both combined in a single `fal-ai/flux-general` call — works
- Image upload to fal CDN via `fal_client.upload_file()` — returns URL for API consumption
- Cost tracking: ~$0.02/frame at 512x512 (~$0.08 for 4-frame cycle)
- Post-processing pipeline (postprocess.py) for background removal, resize, alignment — unchanged from ComfyUI era

## Challenges

### negative_prompt breaks IP-Adapter + ControlNet combo

When using `negative_prompt` together with `ip_adapters` AND `controlnet_unions`, fal.ai returns 422 "Could not load pipeline due to error:". Each feature works individually with negative_prompt, but the triple combination fails. Root cause: fal.ai auto-enables `use_real_cfg` for XLabs IP-Adapter v1, which conflicts with negative prompt processing when ControlNet is also active.

**Fix:** Don't use `negative_prompt` when combining IP-Adapter + ControlNet.

### IP-Adapter weight_name required

The `ip_adapters` config requires `weight_name: "ip_adapter.safetensors"` explicitly. Without it, the pipeline crashes with `'NoneType' object has no attribute 'split'` — the code tries to parse the weight filename but it's None when omitted.

### Small reference images don't work for IP-Adapter

Using the production 40x40 pixel `idle.png` as IP-Adapter reference produced results that looked nothing like the character. IP-Adapter needs a larger, detailed reference image (512x512+) to extract meaningful identity features. Using the raw 1024x1024 AI-generated concept art (`brian_idle_1.png`) produced much better character consistency.

### ControlNet Union pose mode is unreliable (biggest issue)

OpenPose stick figure skeletons (designed for ComfyUI's dedicated OpenPose ControlNet) don't translate well to fal.ai's FLUX ControlNet Union "pose" mode:

- Generated characters have wildly inconsistent scale and position across frames
- Walk poses are barely reflected in the output
- Some frames get random backgrounds despite no background being requested
- Character framing varies dramatically between frames

The ControlNet Union is a multi-purpose model (canny, depth, pose, blur, etc.) — jack-of-all-trades, not a specialist. The dedicated OpenPose ControlNet was purpose-built for pose interpretation.

### Style consistency across frames

Even with higher weights (IP-Adapter 0.8, ControlNet 0.9), generated frames have inconsistent art style, character scale, background presence, and composition.

## Potential Next Steps

1. **Try dedicated ControlNet models** — `controlnets` parameter (not union) might support models that interpret OpenPose better
2. **Image-to-image approach** — use existing idle sprite as base, have model modify pose rather than generating from scratch
3. **Fall back to OpenAI** — the original run sprites were generated with OpenAI + detailed pose descriptions, which produced more consistent results
4. **Try EasyControl** — `easycontrols` parameter has built-in `pose` and `subject` modes that might be simpler
5. **Try fal-ai/instant-character** — dedicated character consistency model

## Model Reference

| Component | Path | Notes |
|-----------|------|-------|
| Main model | `fal-ai/flux-general` | Supports IP-Adapter + ControlNet + LoRA |
| IP-Adapter | `XLabs-AI/flux-ip-adapter` | Requires `weight_name: "ip_adapter.safetensors"` |
| Image encoder | `openai/clip-vit-large-patch14` | Standard CLIP encoder |
| ControlNet Union | `InstantX/FLUX.1-dev-Controlnet-Union` | `control_mode: "pose"` for OpenPose |
| Pricing | ~$0.075/megapixel | ~$0.02/frame at 512x512 |
