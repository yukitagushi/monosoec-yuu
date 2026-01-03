# ExecPlan（計画テンプレ）
Purpose / Big Picture
- ローカルで操作できるMVP（Projects/Jobs/承認/素材出力/ログ/課金）を実装し、UIから一連の流れが体験可能な状態にする。
- 生成の核は動画合成（Render Worker）で、PDF+音声ZIPからMP4を実生成する。
- UIはNotion風の最小構成を維持し、日本語UI・Noto Sans JPに統一する。

Progress
- UIモックとAPIスケルトン実装済み。
- prompts/ ディレクトリが存在しないため、spec/ に現状を記載。

Surprises & Discoveries
- prompts/ が存在しないため、LLM/TTSはスタブ前提とする。

Decision Log
- MVPのDBはSQLiteで先行実装し、後続でPostgresへ差し替える。
- Job状態は QUEUED → RUNNING_RENDER → NEEDS_REVIEW → APPROVED/REJECTED を採用。
- ファイル保存はローカルdata/配下で行い、後でS3に差し替える。

Plan of Work
1) Web/API
   - Projects/JobsのCRUD、Job詳細、アップロード/承認/差戻しのUIを実装
   - APIからの取得/更新を行い、UIモックから動くMVPへ移行
   - 受け入れ条件: UIからジョブ作成→アップロード→レンダリング→承認/差戻しが通る

2) Worker（生成パイプライン）
   - worker/render_worker.sh をAPIから呼び出し、MP4生成まで実行
   - 受け入れ条件: PDF + audio.zip が揃うとMP4が生成され、Artifactとして保存される

3) DB/Storage
   - SQLiteに projects/jobs/artifacts/reviews/audit_logs/billing_usage を追加
   - 受け入れ条件: Project/Job/Artifact/Review/Log/Usage が保存され取得できる

4) Auth/RBAC
   - MVPは固定ユーザーで監査ログを記録

5) Billing
   - 生成動画尺を取得し usage に保存

6) AuditLog
   - 作成/アップロード/レンダ/承認/差戻しの履歴を記録

Concrete Steps
- spec/ に prompts 未定義の記録を追加
- SQLiteストア拡張（projects/jobs/artifacts/reviews/audit_logs/billing_usage）
- FastAPI: CRUD, upload, render起動, artifact配信, approval
- Web: API接続、ジョブ作成/アップロード/承認/DL
- READMEに起動手順と利用手順を追記

Validation and Acceptance
- API: /docs で確認可能
- UI: `python3 -m http.server` で配信しジョブ作成〜承認まで確認可能
- Render: worker/render_worker.sh が実行されMP4が生成

Interfaces and Dependencies
- FastAPI / uvicorn
- SQLite（ローカル）
- FFmpeg / pdftoppm / ffprobe
- Google Fonts (Noto Sans JP)
