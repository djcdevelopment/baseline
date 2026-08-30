"""
Game Client Mailbox Deployment Tool (Transport-Only).

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.

This tool is TRANSPORT ONLY:
  - Validates schema, payload checksums, and contract integrity before dispatch.
  - Performs an atomic write (.tmp write -> fsync -> atomic swap) into the BepInEx runtime inbox.
  - DOES NOT claim installation succeeded or substitute for runtime authority.
  - Success condition: "A validated transport request/artifact was atomically delivered to the runtime inbox."
  - ComfyQuestRuntime remains the sole authority for admission, activation, and QuestReceipt/v1 emission.
"""

import json
import os
import sys
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from tools.contracts.meta_creator_contracts import (
    ContractValidationError,
    validate_comfy_quest_experience,
)
from tools.contracts.quest_compiler import build_install_request

DEFAULT_INBOX_DIR = Path(
    os.getenv(
        "COMFY_QUEST_INBOX_DIR",
        "C:/Program Files (x86)/Steam/steamapps/common/Valheim/BepInEx/config/comfy-quest-runtime/inbox"
    )
)


def deliver_to_mailbox(
    questpack: Dict[str, Any],
    inbox_dir: Optional[Path] = None,
    requested_by: str = "quest_studio_deployer",
    source_revision: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atomically delivers a validated questpack to the target BepInEx runtime inbox.

    Returns a Transport Delivery Receipt dict containing:
      - delivery_id
      - quest_id
      - source_revision
      - compiled_quest_revision
      - install_request_id
      - destination_path
      - payload_sha256
      - delivered_at
      - status: 'delivered_to_inbox'

    Raises ContractValidationError or IOError on validation or write failure.
    """
    # 1. Validate contract integrity
    validate_comfy_quest_experience(questpack)

    quest_id = questpack["quest_id"]
    payload_sha256 = questpack["checksum_sha256"]
    compiled_quest_revision = f"sha256:{payload_sha256}"
    src_rev = source_revision or ("0" * 40)

    # 2. Build InstallQuestPack request payload
    compiled_info = {
        "source_revision": src_rev,
        "compiled_quest_revision": compiled_quest_revision,
        "questpack_payload_sha256": payload_sha256,
    }
    install_req = build_install_request(compiled_info, requested_by=requested_by)

    # Combine request + questpack into full inbox delivery package
    delivery_package = {
        "install_request": install_req,
        "questpack": questpack,
    }

    # 3. Determine target inbox path
    target_dir = inbox_dir or DEFAULT_INBOX_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = "".join(c for c in quest_id if c.isalnum() or c in ("_", "-")).lower()
    target_file = target_dir / f"{safe_filename}.questpack.json"
    temp_file = target_file.with_suffix(".tmp")

    # 4. Atomic Write (.tmp write -> fsync -> rename)
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(delivery_package, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # Atomic swap
        if target_file.exists():
            target_file.unlink()
        temp_file.rename(target_file)
    except Exception as e:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        raise IOError(f"Failed to deliver questpack to runtime inbox: {str(e)}") from e

    delivery_id = f"del_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc).isoformat()

    return {
        "delivery_id": delivery_id,
        "quest_id": quest_id,
        "source_revision": src_rev,
        "compiled_quest_revision": compiled_quest_revision,
        "install_request_id": install_req["request_id"],
        "destination_path": str(target_file),
        "payload_sha256": payload_sha256,
        "delivered_at": now,
        "status": "delivered_to_inbox",
        "transport_note": "Transport request delivered atomically. Runtime admission pending ComfyQuestRuntime execution.",
    }


def main():
    """CLI entrypoint for deploy_questpack."""
    import argparse
    parser = argparse.ArgumentParser(description="Deliver compiled .questpack atomically to BepInEx inbox.")
    parser.add_argument("questpack_path", help="Path to compiled .questpack JSON file")
    parser.add_argument("--inbox-dir", help="Target BepInEx inbox directory override")
    parser.add_argument("--requested-by", default="cli_operator", help="Requesting agent/user identity")
    args = parser.parse_args()

    qp_file = Path(args.questpack_path)
    if not qp_file.exists():
        print(f"Error: questpack file not found: {qp_file}", file=sys.stderr)
        sys.exit(1)

    with open(qp_file, "r", encoding="utf-8") as f:
        questpack_data = json.load(f)

    # Handle compiled output structure if wrapped
    if "questpack" in questpack_data and isinstance(questpack_data["questpack"], dict):
        questpack = questpack_data["questpack"]
        source_rev = questpack_data.get("source_revision")
    else:
        questpack = questpack_data
        source_rev = None

    inbox = Path(args.inbox_dir) if args.inbox_dir else None
    try:
        receipt = deliver_to_mailbox(
            questpack=questpack,
            inbox_dir=inbox,
            requested_by=args.requested_by,
            source_revision=source_rev,
        )
        print(json.dumps(receipt, indent=2))
    except (ContractValidationError, IOError) as err:
        print(f"Deployment Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
