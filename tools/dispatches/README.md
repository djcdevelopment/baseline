# Discord dispatches

`#dispatches` is the editorial source for Baseline's public update feed. It is separate
from `#general` (conversation) and `#workbench` (questions, bugs, and task ownership).

A forum starter post is one dispatch. Its title, body, attachments, author, applied
audience tags, and single format tag are colocated in Discord. Replies remain Discord
conversation and are never syndicated.

The channel topic tells authors the public contract before they post:

> A starter post is syndicated to the web and RSS; replies stay here. Choose at least
> one audience tag and exactly one format tag.

Multiple audience tags are encouraged. They decide which role-specific tables of
contents include the post; they do not hide it from anyone.

```powershell
python tools/dispatches/dispatches.py check
python tools/dispatches/dispatches.py plan
python tools/dispatches/dispatches.py apply --yes
python tools/dispatches/dispatches.py capture
```

`plan` is read-only. `apply` owns only the forum's managed settings and tags; it never
creates, edits, replies to, or deletes a post. `capture` writes the public mirror at
`corpus/mirrors/discord/dispatches.json`. A malformed starter post is retained in the
mirror with `publishable: false` and reasons, but cannot enter RSS or a projection.

Credentials use the existing Workbench bot loader. They remain outside the repo under
`~/.baseline/discord.env` (or the documented environment-variable override).
