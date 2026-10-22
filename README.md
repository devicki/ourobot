[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [繁體中文](README.zh-TW.md)

# Ourobot

## What is Ourobot?

Ourobot is a consultant [Grok Bot](https://grok.com). Other bots (for example Herdrbot or Feedhand) and their owner call it when they are stuck, need a deeper analysis, want fuzzy requirements turned into a clear spec, or want work verified with concrete improvement points. Under the hood it drives [Ouroboros](https://github.com/Q00/ouroboros), a spec-first "Agent OS" for AI coding.

Default mode is **consult + verify**. Building code happens only on explicit request.

## Architecture

| Part | Role |
|---|---|
| Ouroboros MCP server (`ouroboros mcp serve --transport stdio`) | Orchestrator: interview state, seeds, evaluation pipeline. No LLM of its own. |
| Claude Code (`claude`) | LLM backend (`llm.backend: claude_code`): questions, ambiguity scoring, seeds, QA and evaluation judgments. |
| Grok Build CLI (`grok`) | Runtime (`orchestrator.runtime_backend: grok`): writes and runs code during `execute_seed`. |
| This repo (`bin/`) | Small clients so a bot can call the MCP tools from a shell, non-interactively. |

All of it runs on the bot's own Linux box. The bot's skills call the scripts in `~/.ourobot/engine`.

## Install

```bash
git clone https://github.com/devicki/ourobot ~/.ourobot/engine
~/.ourobot/engine/bin/install.sh          # add --upgrade to upgrade ouroboros-ai
```

The installer is idempotent. It installs uv, `ouroboros-ai[mcp]`, the Grok Build CLI and Claude Code if missing, runs `ouroboros setup --runtime grok --non-interactive` only when `~/.ouroboros/config.yaml` does not exist, and prints a status summary. It never logs in and never prints secrets.

## Login (once, by the owner)

```bash
grok login --device-auth     # open the printed URL, confirm the code
claude auth login            # Claude subscription login
```

If the box is reset, run the installer and both logins again.

## Usage

Run the clients with Ouroboros's Python (it ships the `mcp` package): `~/.local/share/uv/tools/ouroboros-ai/bin/python`.

```bash
P=~/.local/share/uv/tools/ouroboros-ai/bin/python; E=~/.ourobot/engine/bin
$P $E/ouro_mcp.py doctor                       # binaries + logins, JSON, exit 0 when ok
$P $E/ouro_mcp.py list-tools [--schema]
$P $E/ouro_mcp.py --timeout 300 call ouroboros_lateral_think \
   --json '{"problem_context":"...","current_approach":"...","persona":"contrarian"}'
$P $E/ouro_mcp.py call ouroboros_qa --args-file args.json

$P $E/interview.py start "idea or context" [--cwd DIR]   # -> session_id + first question
$P $E/interview.py answer <session_id> "answer"         # -> next question
$P $E/interview.py status <session_id>
$P $E/interview.py seed <session_id>                    # ouroboros_generate_seed
```

Useful tools: `ouroboros_interview`, `ouroboros_generate_seed` (also accepts `session_context` without an interview), `ouroboros_qa`, `ouroboros_evaluate`, `ouroboros_lateral_think` (personas: hacker, researcher, simplifier, architect, contrarian), `ouroboros_execute_seed`, `ouroboros_evolve_step`, `ouroboros_ralph`.

For real test evidence in `ouroboros_evaluate`, put `.ouroboros/mechanical.toml` in the project (see [examples/mechanical.toml.example](examples/mechanical.toml.example)) or run `ouroboros detect`. Without it, Stage 1 reports "NO CHECKS EXECUTED" and criteria stay unverified.

## Safety rules

- Default is consult and verify only. `execute_seed` runs only when explicitly requested, only inside an Ouroboros worktree/branch, and Ourobot never merges, pushes or deploys.
- `evolve` and `ralph` loops are token heavy: only on explicit request.
- Never print or store tokens, API keys or login files. Logins are done by the owner.
- Other bots may call Ourobot without asking the owner; Ourobot replies to the requester and sends the owner a short summary.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Credits

Built on [Q00/ouroboros](https://github.com/Q00/ouroboros) (MIT). Ourobot is an independent wrapper and is not affiliated with the Ouroboros project. Licensed under MIT.
