#!/usr/bin/env python3
"""Provision and capture the Discord forum that acts as Baseline's dispatch feed.

This tool manages structure and reads starter posts. It has no code path that creates,
edits, replies to, pins, archives, or deletes a post.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_CONFIG = HERE / "config.json"
DEFAULT_STATE = HERE / "provision-state.json"
WORKBENCH_DISCORD = ROOT / "tools" / "workbench" / "discord"
sys.path.insert(0, str(WORKBENCH_DISCORD))

from workbench_discord import (  # noqa: E402
    CHANNEL_FLAG_REQUIRE_TAG,
    CHANNEL_TYPE_FORUM,
    DiscordClient,
    HttpTransport,
    ToolError,
    load_token,
)


SORT_ORDERS = {"recent_activity": 0, "creation_date": 1}
FORUM_LAYOUT_LIST = 1
TAG_LIMIT = 20
TAG_NAME_LIMIT = 20


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError(f"cannot read {path}: {exc}") from exc


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_config(path: Path) -> dict[str, Any]:
    cfg = read_json(path)
    if cfg.get("schema_version") != 1:
        raise ToolError("dispatch config schema_version must be 1")
    for key in ("guild_id", "bot_id", "mirror"):
        if not isinstance(cfg.get(key), str) or not cfg[key].strip():
            raise ToolError(f"dispatch config {key} must be a non-empty string")
    channel = cfg.get("channel")
    if not isinstance(channel, dict):
        raise ToolError("dispatch config channel must be an object")
    for key in ("name", "topic", "sort_order"):
        if not isinstance(channel.get(key), str) or not channel[key].strip():
            raise ToolError(f"dispatch config channel.{key} must be a non-empty string")
    if channel["sort_order"] not in SORT_ORDERS:
        raise ToolError(f"unknown sort order: {channel['sort_order']}")
    audiences = cfg.get("audience_tags")
    formats = cfg.get("format_tags")
    if not isinstance(audiences, dict) or not audiences:
        raise ToolError("dispatch config audience_tags must be a non-empty object")
    if not isinstance(formats, list) or not formats:
        raise ToolError("dispatch config format_tags must be a non-empty array")
    names = list(audiences) + formats
    if len(names) > TAG_LIMIT:
        raise ToolError(f"dispatch config declares {len(names)} tags; Discord permits {TAG_LIMIT}")
    if len(names) != len(set(names)):
        raise ToolError("dispatch audience and format tag names must be unique")
    too_long = [name for name in names if not isinstance(name, str) or len(name) > TAG_NAME_LIMIT]
    if too_long:
        raise ToolError(f"invalid or over-{TAG_NAME_LIMIT}-character tag names: {too_long}")
    corpus_audiences = read_json(ROOT / "corpus" / "audiences.json")
    known_roles = {role["id"] for role in corpus_audiences.get("roles", [])}
    unknown = sorted(set(audiences.values()) - known_roles)
    if unknown:
        raise ToolError(f"dispatch config maps tags to unknown corpus audiences: {', '.join(unknown)}")
    mirror = (ROOT / cfg["mirror"]).resolve()
    try:
        mirror.relative_to(ROOT)
    except ValueError as exc:
        raise ToolError("dispatch mirror must remain inside the repository") from exc
    return cfg


def desired_tags(cfg: dict[str, Any]) -> list[str]:
    return list(cfg["audience_tags"]) + list(cfg["format_tags"])


def live_client(token_file: Path | None) -> tuple[DiscordClient, HttpTransport]:
    transport = HttpTransport(load_token(token_file))
    return DiscordClient(transport), transport


def find_forum(client: DiscordClient, cfg: dict[str, Any]) -> dict[str, Any] | None:
    named = [channel for channel in client.guild_channels(cfg["guild_id"]) if channel.get("name") == cfg["channel"]["name"]]
    if len(named) > 1:
        raise ToolError(f"more than one channel is named #{cfg['channel']['name']}")
    if not named:
        return None
    if named[0].get("type") != CHANNEL_TYPE_FORUM:
        raise ToolError(f"#{cfg['channel']['name']} exists but is not a forum; refusing to replace it")
    return named[0]


def forum_payload(cfg: dict[str, Any], live: dict[str, Any] | None = None) -> dict[str, Any]:
    channel = cfg["channel"]
    existing = {tag.get("name"): tag for tag in (live or {}).get("available_tags", [])}
    tags = []
    for name in desired_tags(cfg):
        tag = {"name": name, "moderated": False}
        if existing.get(name, {}).get("id"):
            tag["id"] = existing[name]["id"]
        tags.append(tag)
    # A server admin may add a local tag. Preserve it and its ID; this tool only owns the
    # names in config, and removing a live tag could strip it from existing posts.
    tags.extend(tag for name, tag in existing.items() if name not in desired_tags(cfg))
    flags = int((live or {}).get("flags") or 0)
    if channel.get("require_tag"):
        flags |= CHANNEL_FLAG_REQUIRE_TAG
    else:
        flags &= ~CHANNEL_FLAG_REQUIRE_TAG
    return {
        "name": channel["name"],
        "type": CHANNEL_TYPE_FORUM,
        "topic": channel["topic"],
        "flags": flags,
        "available_tags": tags,
        "default_sort_order": SORT_ORDERS[channel["sort_order"]],
        "default_forum_layout": FORUM_LAYOUT_LIST,
    }


def comparable(payload: dict[str, Any]) -> dict[str, Any]:
    tags = [
        {"id": tag.get("id"), "name": tag.get("name"), "moderated": bool(tag.get("moderated"))}
        for tag in payload.get("available_tags", [])
    ]
    return {
        "name": payload.get("name"), "type": payload.get("type"), "topic": payload.get("topic"),
        "flags": int(payload.get("flags") or 0), "available_tags": tags,
        "default_sort_order": payload.get("default_sort_order"),
        "default_forum_layout": payload.get("default_forum_layout") or FORUM_LAYOUT_LIST,
    }


def plan(client: DiscordClient, cfg: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    live = find_forum(client, cfg)
    target = forum_payload(cfg, live)
    if live is None:
        return None, target, [f"CREATE forum #{cfg['channel']['name']} with {len(target['available_tags'])} tags"]
    changes = []
    before = comparable(live)
    after = comparable(target)
    for key in after:
        if before.get(key) != after.get(key):
            changes.append(f"UPDATE {key}: {before.get(key)!r} -> {after.get(key)!r}")
    return live, target, changes


def save_state(path: Path, cfg: dict[str, Any], forum: dict[str, Any]) -> None:
    doc = {
        "schema_version": 1,
        "guild_id": cfg["guild_id"],
        "channel_id": forum["id"],
        "channel_url": f"https://discord.com/channels/{cfg['guild_id']}/{forum['id']}",
    }
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def all_threads(client: DiscordClient, cfg: dict[str, Any], forum_id: str) -> list[dict[str, Any]]:
    active = [thread for thread in client.active_threads(cfg["guild_id"]) if thread.get("parent_id") == forum_id]
    archived = client.archived_threads(forum_id)
    return sorted({thread["id"]: thread for thread in active + archived}.values(), key=lambda item: int(item["id"]))


def starter_message(client: DiscordClient, thread: dict[str, Any]) -> dict[str, Any]:
    thread_id = str(thread["id"])
    direct = client.message(thread_id, thread_id)
    if direct:
        return direct
    messages = client.first_messages(thread_id, limit=100)
    if not messages:
        raise ToolError(f"forum post {thread_id} ({thread.get('name')}) has no readable starter message")
    return messages[0]


def normalize_attachment(value: dict[str, Any]) -> dict[str, Any]:
    keys = ("id", "filename", "description", "content_type", "size", "url", "height", "width", "duration_secs", "waveform")
    return {key: value.get(key) for key in keys if value.get(key) is not None}


def normalize_embed(value: dict[str, Any]) -> dict[str, Any]:
    # Preserve Discord's embed object. It is part of the public starter post and lets a
    # future projection use fields we do not understand today without changing capture.
    return value


def normalize_post(
    cfg: dict[str, Any], forum: dict[str, Any], thread: dict[str, Any], message: dict[str, Any]
) -> dict[str, Any]:
    tag_by_id = {tag["id"]: tag["name"] for tag in forum.get("available_tags", [])}
    tags = [tag_by_id.get(tag_id, f"unknown:{tag_id}") for tag_id in thread.get("applied_tags", [])]
    audiences = [cfg["audience_tags"][name] for name in tags if name in cfg["audience_tags"]]
    formats = [name for name in tags if name in cfg["format_tags"]]
    content = message.get("content") or ""
    reasons = []
    if not content.strip() and not message.get("attachments") and not message.get("embeds"):
        reasons.append("starter post has no text, attachment, or embed")
    if not audiences:
        reasons.append("starter post needs at least one managed audience tag")
    if len(formats) != 1:
        reasons.append(f"starter post needs exactly one managed format tag (found {len(formats)})")
    author = message.get("author") or {}
    result = {
        "thread_id": str(thread["id"]),
        "message_id": str(message.get("id") or thread["id"]),
        "url": f"https://discord.com/channels/{cfg['guild_id']}/{thread['id']}",
        "title": thread.get("name") or "Untitled dispatch",
        "content": content,
        "created_at": message.get("timestamp"),
        "edited_at": message.get("edited_timestamp"),
        "tags": tags,
        "audiences": audiences,
        "format": formats[0] if len(formats) == 1 else None,
        "author": {
            "id": author.get("id"),
            "username": author.get("username"),
            "global_name": author.get("global_name"),
            "bot": bool(author.get("bot")),
        },
        "attachments": [normalize_attachment(item) for item in message.get("attachments", [])],
        "embeds": [normalize_embed(item) for item in message.get("embeds", [])],
        "reply_count": max(int(thread.get("message_count") or 1) - 1, 0),
        "publishable": not reasons,
        "projection_errors": reasons,
    }
    result["content_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return result


def capture(client: DiscordClient, cfg: dict[str, Any], forum: dict[str, Any]) -> dict[str, Any]:
    posts = [normalize_post(cfg, forum, thread, starter_message(client, thread)) for thread in all_threads(client, cfg, forum["id"])]
    times = [post.get("edited_at") or post.get("created_at") for post in posts]
    times = [value for value in times if value]
    return {
        "schema_version": 1,
        "authority": "Discord forum starter posts; this file is a rebuildable public mirror",
        "guild_id": cfg["guild_id"],
        "channel_id": str(forum["id"]),
        "channel_url": f"https://discord.com/channels/{cfg['guild_id']}/{forum['id']}",
        "source_watermark": max(times) if times else None,
        "starter_posts_only": True,
        "replies_syndicated": False,
        "posts": posts,
    }


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    print(f"config     {rel(args.config)}")
    print(f"guild      {cfg['guild_id']}")
    print(f"channel    #{cfg['channel']['name']} (forum, creation-date order, require-tag)")
    print(f"audiences  {len(cfg['audience_tags'])}: {', '.join(cfg['audience_tags'].values())}")
    print(f"formats    {len(cfg['format_tags'])}: {', '.join(cfg['format_tags'])}")
    print(f"mirror     {cfg['mirror']}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    client, _transport = live_client(args.token_file)
    live, _target, changes = plan(client, cfg)
    print(f"live       {'missing' if live is None else '#' + live['name'] + ' (' + live['id'] + ')'}")
    if changes:
        print("\n".join(changes))
    else:
        print("NOOP       live forum already matches the managed contract")
    print("\nNothing was written to Discord.")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    if not args.yes:
        raise ToolError("apply writes live Discord channel structure and requires --yes")
    cfg = load_config(args.config)
    client, transport = live_client(args.token_file)
    live, target, changes = plan(client, cfg)
    if not changes:
        forum = live
        print("Nothing to do -- Discord already matches the managed contract.")
    elif live is None:
        forum = transport.request("POST", f"/guilds/{cfg['guild_id']}/channels", target)
        print(f"created #{forum['name']} ({forum['id']})")
    else:
        # Discord rejects `type` on some channel modifications; it is already proven above.
        patch = {key: value for key, value in target.items() if key != "type"}
        forum = client.modify_channel(live["id"], patch)
        print(f"updated #{forum['name']} ({forum['id']})")
    assert forum is not None
    save_state(args.state, cfg, forum)
    print(f"state      {rel(args.state)}")
    print(f"source     https://discord.com/channels/{cfg['guild_id']}/{forum['id']}")
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    client, _transport = live_client(args.token_file)
    forum = find_forum(client, cfg)
    if forum is None:
        raise ToolError(f"#{cfg['channel']['name']} does not exist; run apply --yes first")
    doc = capture(client, cfg, forum)
    out = args.out or (ROOT / cfg["mirror"])
    resolved = out.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise ToolError("capture output must remain inside the repository") from exc
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    published = sum(1 for post in doc["posts"] if post["publishable"])
    held = len(doc["posts"]) - published
    print(f"captured   {len(doc['posts'])} starter posts ({published} publishable, {held} held)")
    print(f"mirror     {rel(resolved)}")
    for post in doc["posts"]:
        if not post["publishable"]:
            print(f"HELD       {post['title']}: {'; '.join(post['projection_errors'])}")
    return 0


def self_test() -> int:
    cfg = load_config(DEFAULT_CONFIG)
    fake_forum = {"available_tags": [
        {"id": str(index + 1), "name": name} for index, name in enumerate(desired_tags(cfg))
    ]}
    fake_thread = {"id": "999", "name": "A field note", "applied_tags": ["1", str(len(cfg["audience_tags"]) + 2)], "message_count": 3}
    fake_message = {"id": "999", "content": "A complete dispatch.", "timestamp": "2026-08-08T12:00:00+00:00", "author": {"id": "1", "username": "writer"}}
    post = normalize_post(cfg, fake_forum, fake_thread, fake_message)
    assert post["publishable"] and len(post["audiences"]) == 1 and post["format"] == cfg["format_tags"][1]
    assert post["reply_count"] == 2 and "replies" not in post
    fake_thread["applied_tags"] = ["1"]
    held = normalize_post(cfg, fake_forum, fake_thread, fake_message)
    assert not held["publishable"] and held["format"] is None
    print("dispatch contract self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--token-file", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check").set_defaults(func=cmd_check)
    sub.add_parser("plan").set_defaults(func=cmd_plan)
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--yes", action="store_true")
    apply_parser.set_defaults(func=cmd_apply)
    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--out", type=Path, default=None)
    capture_parser.set_defaults(func=cmd_capture)
    sub.add_parser("self-test").set_defaults(func=lambda _args: self_test())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
