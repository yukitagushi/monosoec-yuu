# Render Worker（動画合成）仕様：参照実装
目的：slides（PDF）＋audio（スライド単位音声）＋任意bgmから、YouTube水準のMP4を安定生成する。
要点：音声途切れ対策として aresample async を適用。連結は再エンコード。faststart付与。

手順（安定版）
1) PDF→PNG（pdftoppm）で slides_png/001.png...を生成（必ず作り直す）
2) 001から順に、音声が存在する番号まで処理（音声が無い番号で停止）
3) 各スライドを 1080p/30fps に統一し、画像フェードインのみ適用
4) 音声はAACに統一し、aresample=async=1:first_pts=0 を必ず適用
5) 連結は concat demuxer を使い、再エンコードしてズレ蓄積を防止
6) BGMは -stream_loop -1 でループし、-shortest で動画長に合わせて停止
7) -movflags +faststart を必ず付与

品質チェック（致命のみ）
- segments_fade が0件ならFAILED
- final_1080p.mp4 が0秒ならFAILED
