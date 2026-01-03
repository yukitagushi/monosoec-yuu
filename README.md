monospec-video-saas（仕様書パック）
目的：法人向け「動画生成SaaS」を、仕様（Spec）からブレずに実装するためのリポジトリ。
運用：このリポジトリをCodexに渡し、spec/・prompts/・ui/ を根拠に実装を進める。

フォルダ
- AGENTS.md：Codexが毎回最初に読む作業ルール（最重要）
- .agent/PLANS.md：設計計画テンプレ
- spec/：要件定義をMVPに落とした正本（機能・非機能・課金・監査）
- prompts/：LLM/TTS用プロンプト（安定出力の肝）
- ui/：Notion風UI仕様（画面遷移・コンポーネント）
- mindmap/：俯瞰（Mermaid）
- samples/：入出力サンプル（JSON、参照実装など）
