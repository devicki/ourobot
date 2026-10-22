[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [繁體中文](README.zh-TW.md)

# Ourobot

## Ourobot은 어떤 봇인가요?

Ourobot(우로봇)은 상담역 [Grok Bot](https://grok.com)이에요. 다른 봇(예: Herdrbot, Feedhand)이나 주인이 막혔을 때, 깊은 분석이 필요할 때, 모호한 요구사항을 명확한 명세로 정리하고 싶을 때, 결과물을 검증하고 구체적인 개선점을 받고 싶을 때 불러요. 내부에서는 AI 코딩용 명세 우선 "Agent OS"인 [Ouroboros](https://github.com/Q00/ouroboros)를 구동해요.

기본 모드는 **상담 + 검증**이에요. 코드 작성은 명시적으로 요청할 때만 해요.

## 구조

| 구성 요소 | 역할 |
|---|---|
| Ouroboros MCP server (`ouroboros mcp serve --transport stdio`) | 오케스트레이터: 인터뷰 상태, 시드, 평가 파이프라인. 자체 LLM은 없어요. |
| Claude Code (`claude`) | LLM 백엔드(`llm.backend: claude_code`): 질문, 모호성 점수, 시드, QA·평가 판단. |
| Grok Build CLI (`grok`) | 런타임(`orchestrator.runtime_backend: grok`): `execute_seed` 중에 코드를 작성하고 실행해요. |
| `bin/` | 봇이 셸에서 MCP 도구를 비대화식으로 부를 수 있게 해주는 작은 클라이언트. |

모두 봇의 리눅스 컴퓨터에서 돌아가요. 봇의 스킬은 `~/.ourobot/engine`의 스크립트를 불러요.

## 설치

```bash
git clone https://github.com/devicki/ourobot ~/.ourobot/engine
~/.ourobot/engine/bin/install.sh          # add --upgrade to upgrade ouroboros-ai
```

설치 스크립트는 여러 번 실행해도 안전해요. uv, `ouroboros-ai[mcp]`, Grok Build CLI, Claude Code가 없으면 설치하고, `~/.ouroboros/config.yaml`이 없을 때만 `ouroboros setup --runtime grok --non-interactive`를 실행한 뒤 상태를 보여줘요. 직접 로그인하지 않고 비밀값을 출력하지 않아요.

## 로그인 (주인이 한 번)

```bash
grok login --device-auth     # open the printed URL, confirm the code
claude auth login            # Claude subscription login
```

컴퓨터가 초기화되면 설치 스크립트와 두 로그인을 다시 실행하세요.

## 사용법

클라이언트는 Ouroboros의 Python(`mcp` 패키지 포함)으로 실행해요: `~/.local/share/uv/tools/ouroboros-ai/bin/python`.

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

주요 도구: `ouroboros_interview`, `ouroboros_generate_seed`(인터뷰 없이 `session_context`도 가능), `ouroboros_qa`, `ouroboros_evaluate`, `ouroboros_lateral_think`(페르소나: hacker, researcher, simplifier, architect, contrarian), `ouroboros_execute_seed`, `ouroboros_evolve_step`, `ouroboros_ralph`.

`ouroboros_evaluate`가 실제 테스트 근거를 갖게 하려면 프로젝트에 `.ouroboros/mechanical.toml`을 두거나([예시](examples/mechanical.toml.example)) `ouroboros detect`를 실행하세요. 없으면 1단계가 "NO CHECKS EXECUTED"로 나오고 기준이 검증되지 않은 채로 남아요.

## 안전 규칙

- 기본은 상담과 검증뿐이에요. `execute_seed`는 명시적 요청이 있을 때만, Ouroboros 워크트리/브랜치 안에서만 실행하고, 머지·푸시·배포는 절대 하지 않아요.
- `evolve`와 `ralph` 루프는 토큰을 많이 써서 명시적 요청이 있을 때만 해요.
- 토큰, API 키, 로그인 파일은 출력하거나 저장하지 않아요. 로그인은 주인이 해요.
- 다른 봇은 주인에게 묻지 않고 Ourobot을 부를 수 있어요. Ourobot은 요청한 봇에 답하고 주인에게 짧은 요약을 보내요.

## 테스트

```bash
python3 -m unittest discover -s tests
```

## 크레딧

[Q00/ouroboros](https://github.com/Q00/ouroboros)(MIT) 위에 만들었어요. Ourobot은 독립적인 래퍼이며 Ouroboros 프로젝트와 관계가 없어요. MIT 라이선스예요.
