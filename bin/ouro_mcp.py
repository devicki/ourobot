#!/usr/bin/env python3
"""Ourobot MCP client for the Ouroboros MCP server.

Run with Ouroboros's own Python (it ships the `mcp` package):
    ~/.local/share/uv/tools/ouroboros-ai/bin/python bin/ouro_mcp.py <command>

Commands:
    doctor                         check binaries and logins (stdlib only; any python works)
    list-tools [--schema]          list MCP tools (optionally with input schemas)
    call <tool> --json '{...}'     call a tool; or --args-file args.json
Options: --timeout SECONDS (default 600), --cwd DIR (server working dir)
Output is JSON on stdout. Secrets are never printed.
"""
import argparse, asyncio, json, os, shutil, subprocess, sys
from pathlib import Path

HOME = Path.home()
os.environ["PATH"] = f"{HOME}/.local/bin:" + os.environ.get("PATH", "")
os.environ.setdefault("OUROBOROS_TELEMETRY", "0")
UV_PY = HOME / ".local/share/uv/tools/ouroboros-ai/bin/python"


def _run(cmd, timeout=30):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return -1, str(e)


def doctor():
    r = {}
    for b in ("uv", "ouroboros", "grok", "claude"):
        path = shutil.which(b)
        ver = _run([b, "--version"])[1].splitlines()[-1:] if path else []
        r[b] = {"found": bool(path), "version": ver[0] if ver else None}
    rc, out = _run(["claude", "auth", "status"]) if r["claude"]["found"] else (1, "")
    try:
        logged = bool(json.loads(out).get("loggedIn"))
    except Exception:  # noqa: BLE001
        logged = '"loggedIn": true' in out
    r["claude_auth"] = "logged_in" if logged else "missing (run: claude auth login)"
    grok_ok = (HOME / ".grok/auth.json").exists() or bool(os.environ.get("XAI_API_KEY"))
    r["grok_auth"] = "present" if grok_ok else "missing (run: grok login --device-auth)"
    r["ouroboros_config"] = (HOME / ".ouroboros/config.yaml").exists()
    r["mcp_python"] = UV_PY.exists()
    r["ok"] = all(v["found"] for k, v in r.items() if isinstance(v, dict)) and logged and grok_ok \
        and r["ouroboros_config"] and r["mcp_python"]
    if not r["ok"]:
        r["hint"] = "run bin/install.sh, then the login commands shown"
    return r


def _content(res):
    out = []
    for c in res.content:
        t = getattr(c, "text", None)
        if t is None:
            out.append({"type": getattr(c, "type", "?")}); continue
        try:
            out.append(json.loads(t))
        except Exception:  # noqa: BLE001
            out.append(t)
    return {"is_error": bool(getattr(res, "isError", getattr(res, "is_error", False))),
            "content": out[0] if len(out) == 1 else out,
            "meta": getattr(res, "structuredContent", None) or getattr(res, "structured_content", None)}


async def _session(fn, cwd):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    p = StdioServerParameters(command=shutil.which("ouroboros") or "ouroboros",
                              args=["mcp", "serve", "--transport", "stdio"],
                              env=dict(os.environ), cwd=cwd)
    with open(os.devnull, "w") as devnull:
        async with stdio_client(p, errlog=devnull) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                return await fn(s)


def _schema(t):
    return getattr(t, "input_schema", None) or getattr(t, "inputSchema", None)


async def list_tools(s, schema=False):
    tools = (await s.list_tools()).tools
    return [{"name": t.name, "description": (t.description or "").split("\n")[0][:200],
             **({"input_schema": _schema(t)} if schema else {})} for t in tools]


async def call(s, tool, args):
    return _content(await s.call_tool(tool, args))


def run_mcp(fn, timeout, cwd=None):
    async def go():
        return await asyncio.wait_for(_session(fn, cwd), timeout)
    return asyncio.run(go())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--cwd", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    lt = sub.add_parser("list-tools"); lt.add_argument("--schema", action="store_true")
    c = sub.add_parser("call"); c.add_argument("tool")
    g = c.add_mutually_exclusive_group(); g.add_argument("--json", default=None); g.add_argument("--args-file")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "doctor":
            r = doctor(); print(json.dumps(r, indent=2)); return 0 if r["ok"] else 1
        if a.cmd == "list-tools":
            r = run_mcp(lambda s: list_tools(s, a.schema), a.timeout, a.cwd)
        else:
            args = json.loads(Path(a.args_file).read_text()) if a.args_file else json.loads(a.json or "{}")
            r = run_mcp(lambda s: call(s, a.tool, args), a.timeout, a.cwd)
        print(json.dumps(r, indent=2, ensure_ascii=False, default=str))
        return 1 if isinstance(r, dict) and r.get("is_error") else 0
    except ModuleNotFoundError:
        print(json.dumps({"error": f"mcp package missing; run with {UV_PY}"})); return 2
    except asyncio.TimeoutError:
        print(json.dumps({"error": f"timeout after {a.timeout}s"})); return 3


if __name__ == "__main__":
    sys.exit(main())
