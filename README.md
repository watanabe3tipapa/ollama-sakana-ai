[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.3.0-green.svg)](https://github.com/watanabe3tipapa/ollama-model-runner)

# Ollama Model Runner & Sakana Chat Ratchet

GradioベースのローカルUIツールです。OllamaのローカルモデルとSakana AI（chat.sakana.ai）を同じインターフェースで切り替えて実行できます。

## 概要

- OllamaローカルモデルとSakana AIをGUIから切り替えて利用可能
- モデル選択、プロンプト入力、パラメータ調整、セッション履歴の保存・参照が可能
- デフォルトモデル: `qwen3.5`
- Ollamaモードはストリーミング出力に対応
- Sakana AIモードはPlaywrightによる自動送信を行う

## 主な機能

- モデル選択（Ollamaに登録されたモデルの選択）
- サンプルプロンプト（要約、質問応答、メール下書きなど）
- パラメータ調整（temperature, top_p, max_new_tokens 等）
- ストリーミング出力（Ollamaモード）
- 履歴保存・参照、出力のダウンロード、実行中のキャンセル
- Sakana AIモードではChromium経由でプロンプトを自動送信

## Ollamaモード（主な操作）

| 機能 | 説明 |
|------|------|
| モデル選択 | ドロップダウンでOllamaに登録されたモデルを選択 |
| サンプルプロンプト | フリートーク、要約、質問応答、メール・メッセージ下書き |
| パラメータ調整 | temperature, top_p, max_new_tokens |
| ストリーミング表示 | 出力を逐次表示 |
| 履歴保存 | セッションごとの履歴を保存・参照 |
| 出力ダウンロード | 出力をテキストファイルとしてダウンロード |
| キャンセル | 実行中のリクエストを中断可能 |

## Sakana AIモード（主な操作）

| 機能 | 説明 |
|------|------|
| 自動送信 | プロンプトをChromiumブラウザでchat.sakana.aiに自動送信 |
| 履歴保存 | 送信したプロンプトを履歴に保存 |

## 必要環境

- Ollamaがローカルで起動していること（デフォルト: `http://localhost:11434`）
- Python 3.8+
- uv（パッケージ管理。参考: https://github.com/astral-sh/uv）
- Playwright（ブラウザ自動化用）

## インストールと実行（READMEに記載されている手順）

依存関係をインストールしてアプリを起動します。READMEに記載された手順は次の通りです。

```bash
# 依存関係のインストール
uv sync

# アプリ起動
uv run python app.py
```

起動後、Webブラウザで `http://localhost:7860` にアクセスしてください。

## 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama APIのエンドポイント |

## ドキュメント

リポジトリに付属するドキュメントや使用例がある場合は、リポジトリ内の docs や付随ファイルを参照してください。

## 開発・保守状態

- 表示されているバージョン: 0.3.0（README内バッジに基づく）
- このリポジトリはアーカイブ扱いではありません（公開リポジトリ情報に基づく）

## ライセンス

このプロジェクトは MIT License の下で配布されています。
