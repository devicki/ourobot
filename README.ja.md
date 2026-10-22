[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [繁體中文](README.zh-TW.md)

# Ourobot

## Ourobot とは？

Ourobot は相談役の [Grok Bot](https://grok.com) です。ほかのボット（例: Herdrbot、Feedhand）やオーナーが、行き詰まったとき、深い分析が必要なとき、あいまいな要件を明確な仕様にしたいとき、成果物を検証して具体的な改善点を知りたいときに呼び出します。内部では、AI コーディング向けの仕様ファーストな「Agent OS」である [Ouroboros](https://github.com/Q00/ouroboros) を動かします。

既定モードは**相談＋検証**です。コードの作成は明示的に依頼されたときだけ行います。

## アーキテクチャ

| 構成要素 | 役割 |
|---|---|
| Ouroboros MCP server (`ouroboros mcp serve --transport stdio`) | オーケストレーター：インタビュー状態、シード、評価パイプライン。独自の LLM は持ちません。 |
| Claude Code (`claude`) | LLM バックエンド（`llm.backend: claude_code`）：質問、あいまいさスコア、シード、QA・評価の判断。 |
| Grok Build CLI (`grok`) | ランタイム（`orchestrator.runtime_backend: grok`）：`execute_seed` でコードを書いて実行します。 |
| `bin/` | ボットがシェルから MCP ツールを非対話で呼ぶための小さなクライアント。 |

すべてボット自身の Linux マシンで動きます。ボットのスキルは `~/.ourobot/engine` のスクリプトを呼び出します。

## インストール

```bash
git clone https://github.com/devicki/ourobot ~/.ourobot/engine
~/.ourobot/engine/bin/install.sh          # add --upgrade to upgrade ouroboros-ai
```

インストーラーは何度実行しても安全です。uv、`ouroboros-ai[mcp]`、Grok Build CLI、Claude Code がなければ入れ、`~/.ouroboros/config.yaml` がないときだけ `ouroboros setup --runtime grok --non-interactive` を実行し、状態を表示します。ログインはせず、秘密情報も表示しません。

## ログイン（オーナーが一度だけ）

```bash
grok login --device-auth     # open the printed URL, confirm the code
claude auth login            # Claude subscription login
```

マシンがリセットされたら、インストーラーと両方のログインをやり直してください。

## 使い方

クライアントは Ouroboros の Python（`mcp` パッケージ同梱）で実行します：`~/.local/share/uv/tools/ouroboros-ai/bin/python`。

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

主なツール：`ouroboros_interview`、`ouroboros_generate_seed`（インタビューなしで `session_context` も可）、`ouroboros_qa`、`ouroboros_evaluate`、`ouroboros_lateral_think`（ペルソナ：hacker、researcher、simplifier、architect、contrarian）、`ouroboros_execute_seed`、`ouroboros_evolve_step`、`ouroboros_ralph`。

`ouroboros_evaluate` に実際のテスト根拠を持たせるには、プロジェクトに `.ouroboros/mechanical.toml` を置く（[例](examples/mechanical.toml.example)）か、`ouroboros detect` を実行します。ない場合、ステージ 1 は「NO CHECKS EXECUTED」となり、基準は未検証のままです。

## 安全ルール

- 既定は相談と検証のみです。`execute_seed` は明示的な依頼があるときだけ、Ouroboros のワークツリー／ブランチ内でのみ実行し、マージ・プッシュ・デプロイは行いません。
- `evolve` と `ralph` のループはトークンを多く消費するため、明示的な依頼があるときだけ行います。
- トークン、API キー、ログインファイルは表示も保存もしません。ログインはオーナーが行います。
- ほかのボットはオーナーに確認せず Ourobot を呼べます。Ourobot は依頼元に返答し、オーナーに短い要約を送ります。

## テスト

```bash
python3 -m unittest discover -s tests
```

## クレジット

[Q00/ouroboros](https://github.com/Q00/ouroboros)（MIT）をベースにしています。Ourobot は独立したラッパーで、Ouroboros プロジェクトとは関係ありません。MIT ライセンスです。
