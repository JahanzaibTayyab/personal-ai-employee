---
name: post-instagram
description: Schedule and publish Instagram posts via Meta Graph API. Use when user wants to post on Instagram, schedule Instagram content, create visual social media posts, or share photos/videos on Instagram.
---

# Post Instagram

Schedule an Instagram post for publishing with media attachments.

## Usage

```
/post-instagram <content> --media <url> [--schedule <datetime>] [--media-type <type>]
```

## Arguments

- `content` (required): Post caption (max 2,200 characters)
- `--media` (required): Media URL (Instagram requires media)
- `--schedule` (optional): When to publish (ISO datetime or "now")
- `--media-type` (optional): image, video, or carousel (default: image)

## Workflow

1. Creates post draft in /Social/Meta/posts/
2. Creates approval request in /Pending_Approval/ (if configured)
3. User approves in Obsidian
4. Instagram media container created via Graph API
5. Post published from container
6. Engagement tracked automatically

## Environment Variables

- META_APP_ID: Meta App ID
- META_APP_SECRET: Meta App Secret
- META_ACCESS_TOKEN: Page access token
- META_IG_USER_ID: Instagram Business Account ID

## Rate Limits

Meta Graph API enforces 200 calls/user/hour.
