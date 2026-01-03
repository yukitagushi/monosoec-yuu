# 生成パイプライン（サーバー実装前提）
Step1 入力検証（NG/個人情報/根拠不足）
Step2 構成案生成（LLM）
Step3 台本生成（LLM：根拠紐付け、スライド単位に分割）
Step4 スライド生成（MVP：テンプレ自動組版 → PDF/PNG連番）
Step5 音声生成（TTS API：スライド単位 001.wav…）
Step6 動画合成（FFmpeg：PNG+WAV→MP4、フェード、BGM、faststart、音声async）
Step7 自動品質チェック（致命のみ）
Step8 保存＆下書き出力（承認待ち）
