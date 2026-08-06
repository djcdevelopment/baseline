#!/bin/bash
# Regenerate /etc/caddy/Caddyfile from ~/gallery/users.txt (lines: name:bcrypthash)
# plus the static-gallery serve config and JSON access logging. Run as derek
# (uses sudo); reloads caddy. Single source of truth = users.txt.
set -e
USERS="$HOME/gallery/users.txt"
[ -s "$USERS" ] || { echo "no users in $USERS — add one: ~/gallery/users.sh add <name>"; exit 1; }
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
# build the basic_auth user lines (tab-indented)
AUTH=$(while IFS=: read -r u h; do [ -n "$u" ] && printf '\t\t%s %s\n' "$u" "$h"; done < "$USERS")
sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
{
	auto_https off
	servers {
		# tailscaled proxies funnel traffic from loopback; trust it so the
		# real visitor IP from X-Forwarded-For is what gets logged as client_ip
		trusted_proxies static 127.0.0.1/32 ::1
		client_ip_headers X-Forwarded-For
	}
}
:8190 {
	bind 127.0.0.1
	basic_auth {
$AUTH
	}
	log {
		output file /var/log/caddy/gallery-access.log {
			roll_size 20MiB
			roll_keep 5
		}
		format json
	}
	handle /api/* {
		reverse_proxy 127.0.0.1:8200 {
			header_up X-Gallery-User {http.auth.user.id}
		}
	}
	handle_path /thumb/* {
		root * /home/derek/bench/results_full/thumb
		file_server
	}
	handle_path /img/* {
		root * /home/derek/bench/results_full/img
		file_server
	}
	handle {
		root * /home/derek/gallery
		@fresh path / *.html /index.json /status.json
		header @fresh Cache-Control "no-cache"
		file_server
	}
}
EOF
sudo systemctl reload caddy || sudo systemctl restart caddy
echo "caddy reloaded — users: $(cut -d: -f1 "$USERS" | paste -sd, -)"
