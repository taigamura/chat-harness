@echo off
REM Launch chat-harness inside WSL
wsl -e bash -c "cd ~/chat-harness && ~/.local/bin/uv run python -m chat_harness %*"
