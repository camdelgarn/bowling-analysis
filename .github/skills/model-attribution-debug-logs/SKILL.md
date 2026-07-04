---
name: model-attribution-debug-logs
description: Determine which model and agent handled a specific chat turn by reading VS Code Copilot Chat debug logs. Use when the user asks what model was called, whether Auto used local Ollama, or which agent handled the turn.
---

# Model Attribution From Chat Debug Logs

## Purpose

Find the exact model and agent used for a specific chat turn using evidence from debug logs.

## Primary Sources

Check these in order:

1. Chat Debug entry metadata for the target request.
2. Session debug log directory at {{VSCODE_TARGET_SESSION_LOG}}.
3. Current session extension host log:
   - /home/*/.config/Code/logs/<timestamp>/window1/exthost/GitHub.copilot-chat/GitHub Copilot Chat.log

## What To Extract

Always report these fields when available:

1. endpoint URL
2. model
3. resolved model
4. request id or ccreq id
5. request channel/agent tag (example: panel/editAgent, copilotLanguageModelWrapper)
6. status (success or cancelled)

## Decision Rules

1. Use resolved model as the source of truth for the final model.
2. If endpoint is http://127.0.0.1:11434, classify as local Ollama.
3. For agent attribution, use the bracketed request channel tag from the log line.
4. If multiple lines exist for one user turn, choose the line that matches the latest timestamp for that turn and clearly state any secondary calls.

## Fast Commands (Linux)

Use terminal search when needed:

- grep -nE 'ccreq:|copilotLanguageModelWrapper|panel/editAgent|resolved model|/v1/chat/completions' <GitHub Copilot Chat.log> | tail -n 120
- nl -ba <GitHub Copilot Chat.log> | sed -n '<start>,<end>p'

## Response Format

Provide a short evidence-based result:

1. Primary agent/channel used
2. Model used
3. Whether it was local Ollama
4. One to three supporting facts from logs

If evidence is incomplete, say exactly what is missing.