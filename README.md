[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.3.0-green.svg)](https://github.com/watanabe3tipapa/ollama-model-runner)

# Ollama Runner & Sakana Chat Ratchet

GradioベースのローカルUIツールで、OllamaモデルとSakana AIを簡単に実行できます。

## 概要

- **Ollama** ローカルモデルと **Sakana AI** (chat.sakana.ai) を同一个画面から切り替え可能
- モデル選択、プロンプト入力、パラメータ調整をGUIで操作可能
- デフォルトモデル: `qwen3.5`
- ストリーミング出力対応（Ollamaモード）
- セッション履歴の保存・参照機能
- プロンプトサンプル（要約、質問応答、メール下書きなど）
- Sakana AIモード: Playwrightで自動送信

## 必要環境

- Ollamaがローカルで起動していること（デフォルト: `http://localhost:11434`）
- Python 3.8+
- [uv](https://github.com/astral-sh/uv)（パッケージ管理）
- Playwright（ブラウザ自動化用）

## インストール・実行

```bash
# 依存関係のインストール
uv sync

# アプリ起動
uv run python app.py
```

起動後、`http://localhost:7860`にアクセスしてください。

## 主要機能

### Ollamaモード
| 機能 | 説明 |
|------|------|
| モデル選択 | ドロップダウンでOllamaに登録されたモデルを選択 |
| サンプルプロンプト | フリートーク、要約、質問応答、メール・メッセージ下書き |
| パラメータ調整 | temperature, top_p, max_new_tokens |
| ストリーミング表示 | 出力を逐次表示 |
| 履歴保存 | セッションごとの履歴を保存・参照 |
| 出力ダウンロード | 出力をテキストファイルとしてダウンロード |
| キャンセル | 実行中のリクエストを中断可能 |

### Sakana AIモード
| 機能 | 説明 |
|------|------|
| 自動送信 | プロンプトをChromiumブラウザでchat.sakana.aiに自動送信 |
| 履歴保存 | 送信したプロンプトを履歴に保存 |

## 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama APIのエンドポイント |

## ライセンス

MIT License