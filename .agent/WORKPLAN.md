# ExecPlan（計画テンプレ）
Purpose / Big Picture
- 参照仕様（spec/・ui/・samples/・mindmap/）に基づき、法人向け動画生成SaaSのMVPを段階実装する。
- 生成パイプラインは「検証→構成→台本→スライド→TTS→合成→品質→下書き」を守る。
- UIは ui/00_ui_principles.md に沿ったNotion風の最小UIを採用する。
- Render Workerは spec/06_render_worker.md と samples/reference_render_worker.sh を忠実に移植し、aresample=async=1:first_pts=0、-movflags +faststart、連結の再エンコードを必須とする。

Progress
- spec/・ui/・samples/・mindmap/ を確認済み。
- prompts/ ディレクトリが存在しないため、以後の実装前に仕様補完または指示の明記が必要。

Surprises & Discoveries
- prompts/ が存在しない（仕様不足の可能性）。

Decision Log
- MVP実装は「Web/API」「Worker」「DB/Storage」「Auth/RBAC」「Billing」「AuditLog」に分割して順番に着手する。
- UIはNotion風の最小構成（Sidebar / Page / Meta）をベースにする。
- Render Workerは参照シェル実装をそのまま移植し、FFmpegの要件を満たす。

Plan of Work
1) Web/API
   - 順番: 1st
   - 成果物:
     - プロジェクト/ジョブ作成・一覧・詳細のAPI
     - ジョブ状態管理（検証/構成/台本/スライド/TTS/合成/品質/下書き）
     - 参照情報(根拠)の登録/バリデーション入力
   - 受け入れ条件:
     - 参照情報なしの生成要求は拒否される。
     - ジョブ状態遷移がパイプライン順を守る。
     - MVP画面からジョブ作成/状態確認ができる。

2) Worker（生成パイプライン）
   - 順番: 2nd
   - 成果物:
     - Step1〜Step8の非同期パイプライン骨格
     - Render Worker（spec/06_render_worker.md + samples/reference_render_worker.sh 移植）
     - 品質チェック（致命のみ）
   - 受け入れ条件:
     - Render Workerで aresample=async=1:first_pts=0 を必須適用。
     - 連結は concat demuxer + 再エンコード。
     - -movflags +faststart を最終出力に適用。
     - segments_fade が0件、または final_1080p.mp4 が0秒でFAILED。

3) DB/Storage
   - 順番: 3rd
   - 成果物:
     - プロジェクト/ジョブ/素材/ログの永続化
     - PDF/PNG/WAV/MP4など成果物ストレージ管理
   - 受け入れ条件:
     - 生成成果物がジョブ単位で一覧取得可能。
     - 素材別（台本/スライド/音声/字幕/画像/動画）の保存ができる。

4) Auth/RBAC
   - 順番: 4th
   - 成果物:
     - 組織/ユーザー/役割/承認者フロー
     - 操作権限の制御（閲覧/編集/承認）
   - 受け入れ条件:
     - 承認フローがジョブ出力に必須となる。
     - 役割に応じたアクセス制御が確認できる。

5) Billing
   - 順番: 5th
   - 成果物:
     - 月額/動画尺ベースの課金計算
     - クレジット消費ログ
   - 受け入れ条件:
     - 動画尺に応じた課金計算が走る。
     - 超過クレジットの利用が記録される。

6) AuditLog
   - 順番: 6th
   - 成果物:
     - 生成リクエスト/承認/出力/課金の監査ログ
   - 受け入れ条件:
     - 重要操作が時系列で追跡できる。

Concrete Steps
- prompts/ の欠落をspec/へ補記するか、必要なプロンプト仕様を追加する。
- Web/API → Worker → DB/Storage → Auth/RBAC → Billing → AuditLog の順で実装。
- 各タスクは「変更ファイル一覧 / 理由 / 実行コマンド / 簡易テスト」を必ず出す。

Validation and Acceptance
- spec/00_requirements_summary.md の必須要件（承認/ブランド統一/RBAC/監査/課金）を満たす。
- spec/02_pipeline_design.md の8ステップを順守。
- spec/06_render_worker.md と samples/reference_render_worker.sh の要件を満たす。
- UIは ui/00_ui_principles.md のNotion風最小構成。

Interfaces and Dependencies
- Render Worker: FFmpeg / pdftoppm / ffprobe 依存。
- TTS API: 外部音声生成API（スライド単位でファイル保存）。
- ストレージ: PDF/PNG/WAV/MP4を保存できるバックエンド。
- 課金: 動画尺・月額・超過クレジット計算。
