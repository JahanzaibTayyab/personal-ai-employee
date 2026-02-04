---
name: post-linkedin
description: Schedule and publish LinkedIn posts for business content and sales lead generation. Use when user wants to post on LinkedIn, schedule LinkedIn content, create social media posts for LinkedIn, or share business updates on LinkedIn.
---

# Post LinkedIn

Schedule a LinkedIn post for publishing with optional scheduling.

## Usage

```
/post-linkedin <content> [--schedule <datetime>]
```

## Quick Start

Run the script to create a post:

```bash
scripts/create_post.py "Your post content here" --schedule "2026-02-04T10:00:00"
```

## Arguments

- `content` (required): Post text content (max 3000 characters)
- `--schedule` (optional): When to publish (ISO datetime or "now")

## Examples

```bash
# Immediate post (requires approval)
scripts/create_post.py "Excited to share our latest product update!"

# Scheduled post
scripts/create_post.py "Weekly tips for productivity" --schedule "2026-02-04T10:00:00"

# JSON output
scripts/create_post.py "Post content" --json
```

## Workflow

1. Run `scripts/create_post.py` with content
2. Script creates post draft in `/Social/LinkedIn/posts/`
3. Script creates approval request in `/Pending_Approval/`
4. User moves file to `/Approved/` in Obsidian
5. Approval watcher triggers LinkedIn API publish
6. Engagement tracked in `/Social/LinkedIn/engagement.md`

## Output

```json
{
  "success": true,
  "post_id": "linkedin_20260204_100000",
  "approval_file": "/Pending_Approval/APPROVAL_social_linkedin_20260204_100000.md",
  "expires_at": "2026-02-05T10:00:00"
}
```

## Rate Limits

LinkedIn enforces max 25 posts/day. Script warns before exceeding.
