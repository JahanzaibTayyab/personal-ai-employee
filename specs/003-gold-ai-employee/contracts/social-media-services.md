# Social Media Services Contract

**Version**: 1.0.0 | **Created**: 2026-02-21

## Overview

Contracts for Meta (Facebook/Instagram) and Twitter/X social media services.

---

# Part 1: Meta Service (Facebook/Instagram)

## Interface: MetaService

### Connection Methods

#### initialize

Initialize connection to Meta Graph API.

**Input**:
```python
def initialize(
    access_token: str = None,  # Default from env
    page_id: str = None
) -> bool
```

**Errors**:
- `MetaAuthenticationError`: Invalid access token
- `PageNotFoundError`: Invalid page ID

---

#### refresh_token

Check and refresh access token if expiring.

**Input**:
```python
def refresh_token() -> bool
```

---

### Posting Methods

#### create_post

Create a post (requires approval).

**Input**:
```python
def create_post(
    content: str,
    platform: Literal["facebook", "instagram", "both"],
    media_urls: list[str] = None,
    scheduled_time: datetime = None,
    correlation_id: str = None
) -> MetaPost
```

**Output**: MetaPost with status="pending_approval"

---

#### publish_post

Publish an approved post.

**Input**:
```python
def publish_post(post_id: str) -> MetaPost
```

**Output**: MetaPost with status="posted" and platform_id populated

**Errors**:
- `PostNotFoundError`: Invalid post_id
- `NotApprovedError`: Post not in approved state
- `MetaRateLimitError`: Rate limit exceeded
- `MetaPublishError`: Failed to publish

---

#### schedule_post

Schedule a post for future publishing.

**Input**:
```python
def schedule_post(
    post_id: str,
    scheduled_time: datetime
) -> MetaPost
```

---

### Engagement Methods

#### get_engagement

Get engagement metrics for a post.

**Input**:
```python
def get_engagement(post_id: str) -> MetaEngagement
```

---

#### check_comments

Check for new comments on recent posts.

**Input**:
```python
def check_comments(
    since: datetime = None,  # Default: 24 hours ago
    keywords: list[str] = None  # Business keywords
) -> list[dict]
```

**Output**:
```python
[{
    "post_id": str,
    "comment_id": str,
    "author": str,
    "content": str,
    "matched_keywords": list[str],
    "timestamp": datetime
}]
```

---

#### get_page_insights

Get page-level analytics.

**Input**:
```python
def get_page_insights(
    start_date: date,
    end_date: date
) -> dict
```

---

### Rate Limiting

#### can_make_request

Check if request is within rate limits.

**Input**:
```python
def can_make_request() -> bool
```

---

#### get_rate_limit_status

Get current rate limit usage.

**Input**:
```python
def get_rate_limit_status() -> dict
```

**Output**:
```python
{
    "calls_made": int,
    "calls_remaining": int,
    "reset_time": datetime,
    "limit": int  # 200 per hour
}
```

---

# Part 2: Twitter Service

## Interface: TwitterService

### Connection Methods

#### initialize

Initialize connection to Twitter API v2.

**Input**:
```python
def initialize(
    api_key: str = None,
    api_secret: str = None,
    access_token: str = None,
    access_secret: str = None,
    bearer_token: str = None
) -> bool
```

---

### Posting Methods

#### create_tweet

Create a tweet (requires approval).

**Input**:
```python
def create_tweet(
    content: str,
    media_paths: list[str] = None,
    reply_to_id: str = None,  # For threads
    correlation_id: str = None
) -> Tweet
```

**Output**: Tweet with status="pending_approval"

**Validation**:
- Content must be <= 280 characters (or warn for Premium)

---

#### create_thread

Create a thread of tweets.

**Input**:
```python
def create_thread(
    tweets: list[str],
    correlation_id: str = None
) -> list[Tweet]
```

---

#### publish_tweet

Publish an approved tweet.

**Input**:
```python
def publish_tweet(tweet_id: str) -> Tweet
```

**Output**: Tweet with status="posted" and twitter_id populated

**Errors**:
- `TweetNotFoundError`: Invalid tweet_id
- `NotApprovedError`: Tweet not in approved state
- `TwitterRateLimitError`: Rate limit exceeded
- `TwitterPublishError`: Failed to publish

---

### Engagement Methods

#### get_engagement

Get engagement metrics for a tweet.

**Input**:
```python
def get_engagement(tweet_id: str) -> TweetEngagement
```

---

#### check_mentions

Check for mentions and replies.

**Input**:
```python
def check_mentions(
    since: datetime = None,
    keywords: list[str] = None
) -> list[dict]
```

**Output**:
```python
[{
    "tweet_id": str,
    "author": str,
    "content": str,
    "matched_keywords": list[str],
    "is_reply": bool,
    "is_mention": bool,
    "timestamp": datetime
}]
```

---

#### check_dms

Check direct messages for business keywords.

**Input**:
```python
def check_dms(
    since: datetime = None,
    keywords: list[str] = None
) -> list[dict]
```

**Note**: Requires elevated API access.

---

### Media Methods

#### upload_media

Upload media for attachment.

**Input**:
```python
def upload_media(
    file_path: str,
    media_type: Literal["image", "video", "gif"]
) -> str  # Returns media_id
```

---

### Rate Limiting

#### get_rate_limit_status

Get current rate limit usage by endpoint.

**Input**:
```python
def get_rate_limit_status() -> dict
```

**Output**:
```python
{
    "tweets_post": {"remaining": int, "reset": datetime},
    "mentions_get": {"remaining": int, "reset": datetime},
    "search": {"remaining": int, "reset": datetime}
}
```

---

## Shared Events

| Event | When | Payload |
|-------|------|---------|
| `post_created` | Draft created | platform, post_id |
| `post_published` | Successfully posted | platform, post_id, platform_id |
| `post_failed` | Publishing failed | platform, post_id, error |
| `engagement_updated` | New engagement | platform, post_id, metrics |
| `keyword_detected` | Comment/mention matches | platform, content, keywords |
| `rate_limit_warning` | Approaching limit | platform, remaining |
| `rate_limit_exceeded` | Hit limit | platform, reset_time |

---

## Watchers

### Meta Engagement Watcher

Monitors Facebook and Instagram for:
- New comments on posts
- Business keyword matches
- Engagement metric updates

**Check interval**: 5 minutes

### Twitter Mention Watcher

Monitors Twitter for:
- Mentions (@username)
- Replies to tweets
- DMs with keywords (if available)

**Check interval**: 5 minutes

Both watchers create action items in `/Needs_Action/{platform}/` when keywords are detected.
