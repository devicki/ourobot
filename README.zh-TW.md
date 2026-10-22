[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [繁體中文](README.zh-TW.md)

# Ourobot

## Ourobot 是什麼？

Ourobot 是一個顧問型 [Grok Bot](https://grok.com)。其他機器人（例如 Herdrbot、Feedhand）或擁有者在卡住、需要深入分析、想把模糊需求整理成明確規格，或想驗證成果並取得具體改善建議時，就會呼叫它。它在底層驅動 [Ouroboros](https://github.com/Q00/ouroboros)——一套以規格優先的 AI 程式開發「Agent OS」。

預設模式是**諮詢＋驗證**。只有在明確要求時才會撰寫程式碼。

## 架構

| 元件 | 角色 |
|---|---|
| Ouroboros MCP server (`ouroboros mcp serve --transport stdio`) | 協調器：訪談狀態、種子（Seed）、評估流程。本身不含 LLM。 |
| Claude Code (`claude`) | LLM 後端（`llm.backend: claude_code`）：提問、模糊度評分、種子、QA 與評估判斷。 |
| Grok Build CLI (`grok`) | 執行環境（`orchestrator.runtime_backend: grok`）：在 `execute_seed` 期間撰寫並執行程式碼。 |
| `bin/` | 讓機器人能從 shell 以非互動方式呼叫 MCP 工具的小型用戶端。 |

全部都在機器人自己的 Linux 電腦上執行。機器人的技能會呼叫 `~/.ourobot/engine` 中的腳本。

## 安裝

```bash
git clone https://github.com/devicki/ourobot ~/.ourobot/engine
~/.ourobot/engine/bin/install.sh          # add --upgrade to upgrade ouroboros-ai
```

安裝程式可重複執行。若缺少 uv、`ouroboros-ai[mcp]`、Grok Build CLI 或 Claude Code 就會安裝；只有在 `~/.ouroboros/config.yaml` 不存在時才執行 `ouroboros setup --runtime grok --non-interactive`，最後顯示狀態摘要。它不會自行登入，也不會印出任何機密。

## 登入（擁有者執行一次）

```bash
grok login --device-auth     # open the printed URL, confirm the code
claude auth login            # Claude subscription login
```

若電腦被重設，請重新執行安裝程式與兩項登入。

## 使用方式

請用 Ouroboros 內附的 Python（含 `mcp` 套件）執行用戶端：`~/.local/share/uv/tools/ouroboros-ai/bin/python`。

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

常用工具：`ouroboros_interview`、`ouroboros_generate_seed`（也可不經訪談直接傳入 `session_context`）、`ouroboros_qa`、`ouroboros_evaluate`、`ouroboros_lateral_think`（角色：hacker、researcher、simplifier、architect、contrarian）、`ouroboros_execute_seed`、`ouroboros_evolve_step`、`ouroboros_ralph`。

若要讓 `ouroboros_evaluate` 取得真正的測試證據，請在專案中放置 `.ouroboros/mechanical.toml`（見[範例](examples/mechanical.toml.example)）或執行 `ouroboros detect`。否則第 1 階段會顯示「NO CHECKS EXECUTED」，驗收標準維持未驗證。

## 安全規則

- 預設只做諮詢與驗證。`execute_seed` 僅在明確要求時、且只在 Ouroboros 的 worktree／分支內執行；Ourobot 絕不合併、推送或部署。
- `evolve` 與 `ralph` 迴圈非常耗用 token，只在明確要求時執行。
- 絕不印出或儲存 token、API 金鑰或登入檔案。登入由擁有者完成。
- 其他機器人可不經擁有者同意直接呼叫 Ourobot；Ourobot 會回覆請求者，並傳一則簡短摘要給擁有者。

## 測試

```bash
python3 -m unittest discover -s tests
```

## 致謝

以 [Q00/ouroboros](https://github.com/Q00/ouroboros)（MIT）為基礎。Ourobot 是獨立的包裝工具，與 Ouroboros 專案無關。採用 MIT 授權。
