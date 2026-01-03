#!/usr/bin/env bash
set -euo pipefail

VOICEVOL="${VOICEVOL:-1.15}"
BGMVOL="${BGMVOL:-0.10}"
FADE="${FADE:-0.35}"
FPS="${FPS:-30}"
WIDTH="${WIDTH:-1920}"
DPI="${DPI:-200}"

PDF="${PDF:-pdf/slides.pdf}"
BGM="${BGM:-bgm/bgm.mp3}"

mkdir -p slides_png segments_fade out

for cmd in ffmpeg ffprobe pdftoppm; do
  command -v "$cmd" >/dev/null || { echo "missing cmd: $cmd"; exit 1; }
done

rm -f slides_png/*.png
pdftoppm -png -r "$DPI" "$PDF" slides_png/slide
i=1
for f in $(ls -1v slides_png/slide-*.png); do
  n=$(printf "%03d" "$i")
  mv "$f" "slides_png/$n.png"
  i=$((i+1))
done

rm -f segments_fade/*.mp4
i=1
while :; do
  n=$(printf "%03d" "$i")
  audio=""
  for ext in wav m4a mp3 aac; do
    [ -f "audio/$n.$ext" ] && audio="audio/$n.$ext" && break
  done
  [ -n "$audio" ] || break
  [ -f "slides_png/$n.png" ] || break

  ffmpeg -y -loop 1 -i "slides_png/$n.png" -i "$audio" \
    -r "$FPS" \
    -vf "scale=${WIDTH}:-2,scale=trunc(iw/2)*2:trunc(ih/2)*2,fade=t=in:st=0:d=$FADE" \
    -c:v libx264 -crf 23 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -ar 48000 \
    -af "aresample=async=1:first_pts=0" \
    -shortest -movflags +faststart \
    "segments_fade/$n.mp4"
  i=$((i+1))
done

count=$(ls -1 segments_fade/*.mp4 2>/dev/null | wc -l | tr -d ' ')
[ "$count" -gt 0 ] || { echo "FAILED: no segments generated"; exit 2; }

rm -f segments_fade/list.txt
for f in $(ls -1v segments_fade/*.mp4); do
  printf "file '%s'\n" "$PWD/$f" >> segments_fade/list.txt
done

ffmpeg -y -f concat -safe 0 -i segments_fade/list.txt \
  -r "$FPS" \
  -c:v libx264 -crf 23 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 \
  -af "aresample=async=1:first_pts=0" \
  -movflags +faststart \
  out/final_1080p.mp4

if [ -f "$BGM" ]; then
  ffmpeg -y -i out/final_1080p.mp4 -stream_loop -1 -i "$BGM" \
    -filter_complex "[0:a]volume=${VOICEVOL}[v];[1:a]volume=${BGMVOL}[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart \
    out/final_1080p_bgm.mp4
fi

echo "DONE"
