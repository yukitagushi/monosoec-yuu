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

## ローカル起動（MVPデモ）

### API
```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### UI
```bash
cd web
python3 -m http.server 5173
```

ブラウザで `http://localhost:5173` を開き、以下の流れで操作します。
1. 新規プロジェクトを作成
2. 新規ジョブを作成
3. ジョブ詳細で `slides.pdf` と `audio.zip` をアップロード
4. レンダリング完了後、成果物（mp4）をダウンロード
5. 承認 or 差戻しでレビュー履歴を確認

## Vercelデプロイ確認
- UI: `https://<your-vercel-domain>/`
- API: `https://<your-vercel-domain>/api/docs`
- ヘルスチェック: `https://<your-vercel-domain>/api/health`
