#!/usr/bin/env python3
"""Drive an Ouroboros interview turn by turn, non-interactively, via the MCP tool
`ouroboros_interview` (no pexpect, no TTY).

Run with Ouroboros's Python:  ~/.local/share/uv/tools/ouroboros-ai/bin/python bin/interview.py ...

    start "<idea / context>" [--cwd DIR]   -> {"session_id", "question"}
    answer <session_id> "<answer>"         -> {"session_id", "question" | "completed"}
    status <session_id>                    -> rounds, ambiguity, last question
    seed <session_id> [--force]            -> calls ouroboros_generate_seed

MCP args used (from the tool schema): initial_context, cwd (start);
session_id, answer, last_question (answer turns). The server may append an
optional "advisory fan-out" block after the question; it is stripped here
(kept in "raw" with --raw). The last question is cached in
~/.ourobot/interviews/<session_id>.json so the transcript keeps real question text.
"""
import argparse, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ouro_mcp  # noqa: E402

STATE = Path.home() / ".ourobot/interviews"
SID = re.compile(r"(interview_[0-9a-zA-Z_]+)")


def parse(text):
    """Split an interview tool response into session id and the visible question."""
    if not isinstance(text, str):
        text = json.dumps(text)
    m = SID.search(text)
    body = text.split("<!--", 1)[0]
    body = re.sub(r"^.*?Session( ID:)?\s*interview_\S+\s*", "", body, count=1, flags=re.S).strip()
    done = bool(re.search(r"(?i)interview (is )?(complete|completed|finished)|ready for seed", text))
    return {"session_id": m.group(1) if m else None, "question": body, "completed": done}


def _call(args, timeout, cwd=None):
    r = ouro_mcp.run_mcp(lambda s: ouro_mcp.call(s, "ouroboros_interview", args), timeout, cwd)
    c = r["content"]
    return r, c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)


def _save(sid, q):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / f"{sid}.json").write_text(json.dumps({"last_question": q}, ensure_ascii=False))


def _last(sid):
    f = STATE / f"{sid}.json"
    return json.loads(f.read_text()).get("last_question") if f.exists() else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--raw", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("context"); s.add_argument("--cwd")
    a = sub.add_parser("answer"); a.add_argument("session_id"); a.add_argument("answer")
    st = sub.add_parser("status"); st.add_argument("session_id")
    sd = sub.add_parser("seed"); sd.add_argument("session_id"); sd.add_argument("--force", action="store_true")
    o = ap.parse_args(argv)

    if o.cmd == "status":
        f = Path.home() / f".ouroboros/data/interview_{o.session_id}.json"
        d = json.loads(f.read_text()) if f.exists() else {}
        out = {"session_id": o.session_id, "found": bool(d), "status": d.get("status"),
               "rounds": len(d.get("rounds", [])), "ambiguity_score": d.get("ambiguity_score"),
               "last_question": _last(o.session_id)}
        print(json.dumps(out, indent=2, ensure_ascii=False)); return 0
    if o.cmd == "seed":
        args = {"session_id": o.session_id, **({"force": True} if o.force else {})}
        r = ouro_mcp.run_mcp(lambda s: ouro_mcp.call(s, "ouroboros_generate_seed", args), o.timeout)
        print(json.dumps(r, indent=2, ensure_ascii=False, default=str)); return 1 if r["is_error"] else 0
    if o.cmd == "start":
        args = {"initial_context": o.context, **({"cwd": o.cwd} if o.cwd else {})}
        r, text = _call(args, o.timeout, o.cwd)
    else:
        args = {"session_id": o.session_id, "answer": o.answer}
        lq = _last(o.session_id)
        if lq:
            args["last_question"] = lq
        r, text = _call(args, o.timeout)
    p = parse(text)
    p["session_id"] = p["session_id"] or getattr(o, "session_id", None)
    p["is_error"] = r["is_error"]
    if p["session_id"] and p["question"]:
        _save(p["session_id"], p["question"])
    if o.raw:
        p["raw"] = text
    print(json.dumps(p, indent=2, ensure_ascii=False))
    return 1 if r["is_error"] else 0


if __name__ == "__main__":
    sys.exit(main())
