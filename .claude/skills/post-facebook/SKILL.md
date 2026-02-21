---
name: post-facebook
description: Schedule and publish Facebook posts via Meta Graph API. Use when user wants to post on Facebook, schedule Facebook content, create social media posts for Facebook, or share business updates on Facebook.
---

# Post Facebook

Schedule a Facebook post for publishing with optional scheduling and media.

## Usage

```
/post-facebook <content> [--schedule <datetime>] [--media <url>] [--cross-post]
```

## Arguments

- `content` (required): Post text content (max 63,206 characters)
- `--schedule` (optional): When to publish (ISO datetime or "now")
- `--media` (optional): Media URL to attach (image or video)
- `--cross-post` (optional): Also post to Instagram
- `--page-id` (optional): Facebook Page ID (uses configured default)

## Workflow

1. Creates post draft in /Social/Meta/posts/
2. Creates approval request in /Pending_Approval/ (if configured)
3. User approves in Obsidian
4. Post published via Meta Graph API
5. Engagement tracked automatically

## Environment Variables

- META_APP_ID: Meta App ID
- META_APP_SECRET: Meta App Secret
- META_ACCESS_TOKEN: Page access token
- META_PAGE_ID: Default Facebook Page ID

## Rate Limits

Meta Graph API enforces 200 calls/user/hour.
