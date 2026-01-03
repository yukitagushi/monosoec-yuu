# 技術スタック & ディレクトリ構成（MVP）

## 技術スタック
- Web: HTML/CSS（Notion風の最小UI。将来のUIフレームワーク差し替え前提）
- API: Python 3.11 / FastAPI / Pydantic
- Worker: Python 3.11（生成パイプライン制御）+ FFmpeg / pdftoppm
- DB: PostgreSQL（RDB）
- Storage: S3互換オブジェクトストレージ
- Infra: Docker Compose（ローカル開発）

## ディレクトリ構成
- web/: Notion風UI（静的UIフレーム）
- api/: FastAPI（API雛形・状態遷移）
- worker/: 生成パイプライン（Render Worker含む）
- infra/: DBスキーマ・Docker Composeなど
