wsl.exe -d oceanbase-desktop -u root -- bash -lc 'pgrep -f "sleep 100000" >/dev/null || setsid nohup sleep 100000 >/dev/null 2>&1 </dev/null & disown'
