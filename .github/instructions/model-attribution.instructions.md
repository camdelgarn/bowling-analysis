---
applyTo: ".github/**"
---

When the user asks which model was used, which agent handled a chat, whether Auto selected a local Ollama model, or similar attribution questions, prioritize the skill `model-attribution-debug-logs`.

Use that skill before giving conclusions.

For these prompts, provide concise evidence-based answers with:

1. Primary agent or request channel used.
2. Final resolved model used.
3. Whether endpoint indicates local Ollama.
4. One to three supporting facts from debug logs.

Example trigger phrases:

- what model is being called
- which agent got used
- did Auto use ollama
- what model did this chat use

If evidence is incomplete, state what is missing and where to look next in debug logs.