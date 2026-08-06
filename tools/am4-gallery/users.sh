#!/bin/bash
# Manage gallery logins. Source of truth: ~/gallery/users.txt (name:bcrypthash).
#   users.sh add <name> [password]   create/replace a user (random pw if omitted)
#   users.sh del <name>              remove a user
#   users.sh list                    list usernames
set -e
USERS="$HOME/gallery/users.txt"
touch "$USERS"
cmd="$1"; name="$2"
case "$cmd" in
  add)
    [ -z "$name" ] && { echo "usage: users.sh add <name> [password]"; exit 1; }
    pw="${3:-$(openssl rand -hex 9)}"
    hash="$(caddy hash-password --plaintext "$pw")"
    grep -v "^$name:" "$USERS" > "$USERS.tmp" 2>/dev/null || true
    echo "$name:$hash" >> "$USERS.tmp"
    mv "$USERS.tmp" "$USERS"
    bash "$HOME/gallery/gen_caddyfile.sh"
    echo
    echo "  user:     $name"
    echo "  password: $pw"
    echo "  url:      https://am4.tail8e749c.ts.net/"
    ;;
  del)
    [ -z "$name" ] && { echo "usage: users.sh del <name>"; exit 1; }
    grep -v "^$name:" "$USERS" > "$USERS.tmp" 2>/dev/null || true
    mv "$USERS.tmp" "$USERS"
    bash "$HOME/gallery/gen_caddyfile.sh"
    echo "removed: $name"
    ;;
  list)
    cut -d: -f1 "$USERS"
    ;;
  *)
    echo "usage: users.sh {add <name> [pw]|del <name>|list}"; exit 1;;
esac
