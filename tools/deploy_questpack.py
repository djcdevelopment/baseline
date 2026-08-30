"""
CLI wrapper for Game Client Mailbox Deployment Tool.

Usage:
  python tools/deploy_questpack.py path/to/questpack.json [--inbox-dir PATH] [--requested-by USER]
"""

from tools.contracts.deploy_questpack import main

if __name__ == "__main__":
    main()
