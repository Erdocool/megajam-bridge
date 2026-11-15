#!/usr/bin/env bash
# fetch_file.sh <remote_path> <local_path> : pull a file from the PC via !py base64 slices (verifies offset, retries)
set -uo pipefail
R="$1"; L="$2"; CH=34000; off=0; : > "$L.part"; size=1
while [ $off -lt $size ]; do
  ok=0
  for try in 1 2 3 4; do
    { printf '!py\nimport base64,os\np=%s\nf=open(p,"rb"); f.seek(%d); b=f.read(%d); f.close()\nprint("SIZE",os.path.getsize(p)); print("OFF %d"); print(base64.b64encode(b).decode())\n#' "'$R'" $off $CH $off; } | /workspace/bridge/send.sh >/dev/null || continue
    for w in 1 2 3; do
      out=$(/workspace/bridge/read.sh --wait 150 2>/dev/null | tr -d '\r')
      echo "$out" | grep -q "^OFF $off\$" && break
    done
    echo "$out" | grep -q "^OFF $off\$" || continue
    size=$(echo "$out" | sed -n 's/^SIZE \([0-9]*\)$/\1/p' | head -1)
    echo "$out" | grep -E '^[A-Za-z0-9+/=]{100,}$' | tr -d '\n' | base64 -d >> "$L.part" && ok=1 && break
  done
  [ $ok = 1 ] || { echo "FAILED at $off"; exit 1; }
  off=$((off+CH))
done
mv "$L.part" "$L"; echo "got $L $(stat -c%s "$L")/$size"
