#!/usr/bin/env bash
# Ourobot engine installer: idempotent install/check of Ouroboros, Grok Build CLI and Claude Code.
# Never logs in, never prints secrets.  Usage: bin/install.sh [--upgrade]
set -u
UPGRADE=0; [ "${1:-}" = "--upgrade" ] && UPGRADE=1
export PATH="$HOME/.local/bin:$PATH"
export OUROBOROS_TELEMETRY="${OUROBOROS_TELEMETRY:-0}"
have(){ command -v "$1" >/dev/null 2>&1; }
say(){ printf '[ourobot] %s\n' "$*"; }

if ! have uv; then say "installing uv"; curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null; export PATH="$HOME/.local/bin:$PATH"; fi

if ! have ouroboros; then say "installing ouroboros-ai[mcp]"; uv tool install 'ouroboros-ai[mcp]'
elif [ $UPGRADE = 1 ]; then say "upgrading ouroboros-ai"; uv tool upgrade ouroboros-ai; fi

if ! have grok; then say "installing Grok Build CLI"; curl -fsSL https://x.ai/cli/install.sh | bash; fi
if ! have claude; then say "installing Claude Code"; curl -fsSL https://claude.ai/install.sh | bash; fi
export PATH="$HOME/.local/bin:$PATH"

if [ ! -f "$HOME/.ouroboros/config.yaml" ]; then
  say "configuring ouroboros (runtime grok)"; ouroboros setup --runtime grok --non-interactive >/dev/null
fi

echo; say "status"
printf '  ouroboros: %s\n' "$(ouroboros --version 2>/dev/null | tail -1 || echo missing)"
printf '  grok:      %s\n' "$(grok --version 2>/dev/null | head -1 || echo missing)"
printf '  claude:    %s\n' "$(claude --version 2>/dev/null | head -1 || echo missing)"
if claude auth status 2>/dev/null | grep -q '"loggedIn": *true'; then echo "  claude auth: logged in"; else echo "  claude auth: NOT logged in -> run: claude auth login"; fi
echo "  grok auth: check with 'python3 bin/ouro_mcp.py doctor'; if needed run: grok login --device-auth"
