# Codex 作業ルール（このリポジトリが仕様の正本）
- 最初に spec/ ui/ prompts/ を読む。矛盾・不足があれば spec/ に追記してから実装へ進む
- 大きい作業は .agent/WORKPLAN.md を .agent/PLANS.md 形式で作る（計画→実装）
- 実装は「Web(API/UI)」「Worker(生成パイプライン)」「Storage/DB」「Auth/Org/RBAC」「Billing」「AuditLog」に分割
- 生成は必ず参照情報に基づく（汎用知識だけで作るのは禁止）。機密・個人情報の扱いに注意
- NotebookLMのスライド生成に強く依存しない。MVPはテンプレ自動組版で代替し、後で差し替え可能にする
- 変更は小さく分割し、各タスクで「変更ファイル一覧 / 理由 / 実行コマンド / 簡易テスト」を必ず出す
