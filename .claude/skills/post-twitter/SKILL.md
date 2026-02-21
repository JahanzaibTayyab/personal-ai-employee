---
name: post-twitter
description: Schedule and publish tweets via Twitter API v2. Use when user wants to tweet, post on Twitter/X, create tweet threads, or schedule Twitter content.
---

# Post Twitter

Schedule a tweet or thread for publishing via Twitter API v2.

## Usage

```
/post-twitter <content> [--schedule <datetime>] [--thread] [--media <ids>]
```

## Arguments

- `content` (required): Tweet text (max 280 characters per tweet)
- `--schedule` (optional): When to publish (ISO datetime or "now")
- `--thread` (optional): Create a thread (separate tweets with ---)
- `--media` (optional): Comma-separated media IDs to attach
- `--reply-to` (optional): Tweet ID to reply to

## Workflow

1. Creates tweet draft in /Social/Twitter/tweets/
2. For threads, creates all tweets with parent references
3. Publishes via Twitter API v2 (tweepy)
4. Engagement tracked automatically
5. Mentions monitored for business keywords

## Environment Variables

- TWITTER_API_KEY: Twitter API key
- TWITTER_API_SECRET: Twitter API secret
- TWITTER_ACCESS_TOKEN: User access token
- TWITTER_ACCESS_SECRET: User access secret
- TWITTER_BEARER_TOKEN: Bearer token for app-only auth

## Rate Limits

Twitter API v2 enforces rate limits per endpoint with automatic backoff.
