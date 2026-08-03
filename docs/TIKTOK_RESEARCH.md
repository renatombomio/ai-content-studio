# TikTok Publisher Research

**Task:** S5-001  
**Date:** 2026-08-03  
**Status:** Research Complete — No code written  

---

## 1. Publishing API

### Which API

**Content Posting API** — the official TikTok API for posting video content programmatically.

Two posting modes exist:

| Mode | Scope | Behaviour |
|------|-------|-----------|
| **Direct Post** | `video.publish` | Posts directly to creator's TikTok profile |
| **Upload to Inbox** | `video.upload` | Sends to creator's inbox as a draft; creator publishes manually |

For automated publishing (Cocoa Talk Studio), **Direct Post** is the correct mode.

### Availability

- **Public:** Yes — listed as an official product on `developers.tiktok.com/products/content-posting-api/`
- **Approval required:** Yes — two levels:
  1. App must be registered on the TikTok for Developers portal
  2. The `video.publish` scope requires explicit app audit and approval
  3. Unaudited apps can only post to `SELF_ONLY` privacy (private videos)
- **Worldwide:** No explicit geographic restrictions documented
- **Personal accounts:** Supported — the API works with any TikTok account type
- **Business accounts:** Not required — standard creator accounts are sufficient

---

## 2. Authentication

### OAuth 2.0 Flow

TikTok uses **Login Kit** — its OAuth 2.0 implementation based on RFC 6749.

**Step 1 — Authorization request**

Redirect the user to:
```
https://www.tiktok.com/v2/auth/authorize/
  ?client_key=<CLIENT_KEY>
  &response_type=code
  &scope=video.publish,user.info.basic
  &redirect_uri=<REDIRECT_URI>
  &state=<RANDOM_CSRF_TOKEN>
```

**Step 2 — User consents**

TikTok redirects back to `redirect_uri`:
```
<REDIRECT_URI>?code=<AUTH_CODE>&scopes=video.publish&state=<STATE>
```

**Step 3 — Exchange code for tokens**

```
POST https://open.tiktokapis.com/v2/oauth/token/

Body:
  client_key=<CLIENT_KEY>
  client_secret=<CLIENT_SECRET>
  code=<AUTH_CODE>
  grant_type=authorization_code
  redirect_uri=<REDIRECT_URI>
```

Response:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "open_id": "...",
  "scope": "video.publish,user.info.basic",
  "expires_in": 86400,
  "refresh_expires_in": 31536000
}
```

**Step 4 — Refresh**

```
POST https://open.tiktokapis.com/v2/oauth/token/

Body:
  client_key=<CLIENT_KEY>
  client_secret=<CLIENT_SECRET>
  grant_type=refresh_token
  refresh_token=<REFRESH_TOKEN>
```

**Step 5 — Revoke**

```
POST https://open.tiktokapis.com/v2/oauth/revoke/
```

### Credentials

| Credential | Description |
|------------|-------------|
| `client_key` | App's unique identifier (referred to as Client ID in some contexts) |
| `client_secret` | App's secret — never expose to clients |
| `redirect_uri` | Must match exactly what is registered in the developer portal |

Mobile/desktop apps also require PKCE (`code_verifier` / `code_challenge`). Server-side apps do not.

### Token Lifetime

| Token | Lifetime |
|-------|----------|
| `access_token` | 24 hours |
| `refresh_token` | 365 days |

### Required Scopes

| Scope | Purpose | Approval Required |
|-------|---------|-------------------|
| `video.publish` | Direct Post to profile | Yes — app audit required |
| `video.upload` | Upload to inbox as draft | Yes |
| `video.list` | Read user's public videos | Not documented |
| `user.info.basic` | Basic profile info | Added by default |

---

## 3. Upload Flow

### Direct Post — Complete Sequence

```
1. GET creator info
   POST /v2/post/publish/creator_info/query/
   → privacy_level_options, duet_disabled, stitch_disabled, comment_disabled,
     max_video_post_duration_sec

↓

2. Initialize upload
   POST /v2/post/publish/video/init/
   Body: { source_info: { source, video_size, chunk_size, total_chunk_count },
           post_info: { title, privacy_level, disable_duet, disable_stitch,
                        disable_comment, video_cover_timestamp_ms } }
   → publish_id, upload_url (valid 1 hour)

↓

3a. FILE_UPLOAD path — PUT chunks to upload_url
    PUT {upload_url}
    Headers: Content-Type: video/mp4
             Content-Range: bytes {start}-{end}/{total}
             Content-Length: {chunk_bytes}
    → 206 Partial Content (intermediate)
    → 201 Created (final chunk)

   OR

3b. PULL_FROM_URL path — no PUT required
    TikTok fetches from the video_url provided in step 2
    (domain must be pre-verified)

↓

4. Poll status
   POST /v2/post/publish/status/fetch/
   Body: { "publish_id": "..." }
   → status field (see §4)

↓

5. PUBLISH_COMPLETE
   → publicaly_available_post_id returned
   → Video visible on profile
```

### All Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `https://www.tiktok.com/v2/auth/authorize/` | GET redirect | OAuth authorization |
| `https://open.tiktokapis.com/v2/oauth/token/` | POST | Token exchange / refresh |
| `https://open.tiktokapis.com/v2/oauth/revoke/` | POST | Revoke token |
| `https://open.tiktokapis.com/v2/post/publish/creator_info/query/` | POST | Query creator capabilities |
| `https://open.tiktokapis.com/v2/post/publish/video/init/` | POST | Initialize Direct Post upload |
| `https://open.tiktokapis.com/v2/post/publish/inbox/video/init/` | POST | Initialize Inbox (draft) upload |
| `{upload_url}` (dynamic) | PUT | Transfer video chunks |
| `https://open.tiktokapis.com/v2/post/publish/status/fetch/` | POST | Poll publication status |

---

## 4. Publication Status

### Status Values

| Status | Phase | Meaning |
|--------|-------|---------|
| `PROCESSING_UPLOAD` | Transfer | File upload in progress (FILE_UPLOAD path) |
| `PROCESSING_DOWNLOAD` | Transfer | TikTok fetching from URL (PULL_FROM_URL path) |
| `SEND_TO_USER_INBOX` | Draft | Sent to inbox; awaiting creator action (Upload mode) |
| `PUBLISH_COMPLETE` | Done | Video live on profile |
| `FAILED` | Error | Process failed; `fail_reason` field populated |

### Polling

**Required** — no webhooks documented.

- Endpoint: `POST /v2/post/publish/status/fetch/`
- Rate limit: **30 requests per minute** per access token
- Progress fields: `uploaded_bytes` / `downloaded_bytes`
- Final field on success: `publicaly_available_post_id`

**Processing times** (documented estimates):
- 512 MB video: < 30 seconds
- 4 GB video: > 2 minutes
- Moderation: typically < 1 minute, may extend to a few hours

---

## 5. Metadata

### Supported Fields (Direct Post — `video.publish`)

| Field | Type | Notes |
|-------|------|-------|
| `title` | string | Caption text. Hashtags (#) and mentions (@) parsed automatically. Max 2200 UTF-16 runes. |
| `privacy_level` | enum | `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `FOLLOWER_OF_CREATOR`, `SELF_ONLY`. Must use values returned by creator_info. No default allowed. |
| `disable_comment` | boolean | `true` = comments off |
| `disable_duet` | boolean | `true` = duet off |
| `disable_stitch` | boolean | `true` = stitch off |
| `video_cover_timestamp_ms` | int32 | Frame position in milliseconds for thumbnail |
| `brand_content_toggle` | boolean | `true` = paid partnership disclosure |
| `brand_organic_toggle` | boolean | `true` = promoting creator's own brand |
| `is_aigc` | boolean | `true` = AI-generated content label |

### Constraints

- Hashtags and mentions are embedded in `title` (no separate hashtag array)
- `privacy_level` must come from `creator_info` response — do not hardcode
- If creator has `duet_disabled=true` or `stitch_disabled=true` in their account settings, those fields cannot be enabled regardless of what is sent
- Duet/Stitch fields not applicable to photo posts
- `video_cover_timestamp_ms` is optional; TikTok picks cover automatically if omitted

---

## 6. Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `video/init/` (Direct Post) | 6 req/min | per access token, 1-min sliding |
| `inbox/video/init/` (Upload) | 6 req/min | per access token, 1-min sliding |
| `status/fetch/` | 30 req/min | per access token, 1-min sliding |
| `creator_info/query/` | 20 req/min | per access token, 1-min sliding |
| `/v2/user/info/` | 600 req/min | documented in v2 rate limit guide |

### Daily Limits

- **5 pending inbox shares** per user per 24-hour window (Upload mode)
- No documented daily cap on Direct Post, but spam detection is active

### Exceeding Limits

HTTP 429 returned with `error.code = "rate_limit_exceeded"`.  
Apps needing higher limits must contact TikTok support.

---

## 7. Error Handling

### Error Response Format (API v2)

All errors return:
```json
{
  "error": {
    "code": "error_code_string",
    "message": "Human readable description",
    "log_id": "unique_request_id"
  }
}
```

### Authentication Errors

| Code | HTTP | Cause | Action |
|------|------|-------|--------|
| `access_token_invalid` | 401 | Token expired or missing | Refresh token and retry |
| `scope_not_authorized` | 401 | User did not grant required scope | Re-initiate OAuth with correct scope |
| `scope_permission_missed` | 400 | Token lacks scope for specific field | Request elevated scope |

### Upload Errors

| Code | HTTP | Cause | Action |
|------|------|-------|--------|
| `invalid_file_upload` | 400 | File format/size not meeting spec | Validate before upload |
| `url_ownership_unverified` | 403 | Domain not verified (PULL_FROM_URL) | Verify domain in dev portal |
| — | 403 | Upload URL expired (>1 hour) | Re-initialize upload |
| — | 416 | Mismatched `Content-Range` header | Fix chunk calculation |
| — | 5xx | Server error | Retry with exponential backoff |

### Validation Errors

| Code | HTTP | Cause | Action |
|------|------|-------|--------|
| `invalid_params` | 400 | Field value invalid | Read error.message for specific field |
| `spam_risk_too_many_pending_share` | 403 | 5-share daily cap hit | Wait 24 hours |
| `spam_risk_user_banned_from_posting` | 403 | Account posting ban | Surface to user |

### Rate Limit Errors

| Code | HTTP | Cause | Action |
|------|------|-------|--------|
| `rate_limit_exceeded` | 429 | Per-minute quota exceeded | Exponential backoff, respect sliding window |

### Server Errors

| Code | HTTP | Cause | Action |
|------|------|-------|--------|
| `internal_error` | 500 | TikTok internal error | Log `log_id`, retry; contact support if persistent |

---

## 8. Best Practices

### Retries

- **5xx errors:** Retry with exponential backoff (e.g., 1s → 2s → 4s)
- **429:** Respect the 1-minute sliding window before retrying
- **401 `access_token_invalid`:** Refresh token first, then retry once
- Do not retry 400 or 403 errors without fixing the underlying cause

### Large Uploads

- Chunk size: minimum 5 MB, maximum 64 MB (final chunk up to 128 MB)
- Maximum 1,000 chunks per upload
- For files < 5 MB: upload as single chunk with `chunk_size = video_size`
- Upload URL expires after **1 hour** — must complete all chunks in this window
- Recommended format: **MP4 + H.264 codec**
- HTTPS only — TikTok does not follow HTTP redirects

### Polling

- Poll `status/fetch/` with backoff — not tight loops
- Suggested interval: every 3–5 seconds for the first minute, then every 10–30 seconds
- Stop polling on `PUBLISH_COMPLETE` or `FAILED`
- Max 30 polls/min — budget carefully for concurrent uploads

### Token Storage

- Store `access_token` and `refresh_token` encrypted at rest
- Never log tokens
- Refresh `access_token` before expiry (24h TTL) — refresh proactively at 20–22h
- `refresh_token` lasts 365 days — prompt re-auth when approaching expiry
- Use `client_secret` only server-side

### Security

- Validate `state` parameter on OAuth callback to prevent CSRF
- Use PKCE (`code_verifier`) for mobile/desktop apps
- Restrict `redirect_uri` to exact registered values
- Treat `publish_id` and `open_id` as sensitive identifiers — do not expose in logs

---

## 9. Cocoa Studio Design Recommendations

Based solely on this research.

### Publication Model

Two concepts map to TikTok's two modes:

**`PublicationJob`** — represents a single publication attempt with:
- `publish_id` (returned from TikTok)
- `status` (mirrors TikTok states: `PENDING`, `PROCESSING_UPLOAD`, `PROCESSING_DOWNLOAD`, `PUBLISH_COMPLETE`, `FAILED`)
- `post_metadata` (title, privacy_level, disable_duet, disable_stitch, disable_comment, video_cover_timestamp_ms)
- `created_at`, `updated_at`, `tiktok_post_id` (populated on success)

**`TikTokCredentials`** — stored per authorized account:
- `open_id`
- `access_token` (encrypted)
- `refresh_token` (encrypted)
- `access_token_expires_at`
- `refresh_token_expires_at`
- `granted_scopes`

### Publisher Interface

```
Publisher (abstract)
  publish(video_path, metadata) → PublicationJob
  get_status(publish_id) → PublicationStatus
  refresh_credentials() → TikTokCredentials
```

### TikTokPublisher Responsibilities

1. **Token management** — refresh `access_token` before every API call if within 2h of expiry
2. **Creator info** — call `creator_info/query/` before each publish to get live `privacy_level_options`
3. **Upload initialization** — call `video/init/` with metadata and source info
4. **File transfer** — chunk video file and PUT to `upload_url` with correct `Content-Range` headers
5. **Status reporting** — return `publish_id` immediately; do not block on completion
6. **Error mapping** — translate TikTok error codes to internal `PublisherError` types

### PublicationService Responsibilities

1. **Orchestration** — coordinate `TikTokPublisher` calls in sequence
2. **Polling loop** — background job polls `status/fetch/` at sensible intervals until terminal state
3. **Retry logic** — wrap 5xx and 429 errors with exponential backoff
4. **Credential refresh** — call `TikTokPublisher.refresh_credentials()` on 401, then retry once
5. **Status persistence** — write `PublicationJob` state to storage after each poll
6. **Notification** — emit event or update job record when `PUBLISH_COMPLETE` or `FAILED`

### Key Design Decisions

- Use **Direct Post** (`video.publish`) not Inbox — automated pipeline requires no manual step
- Retrieve `privacy_level_options` dynamically — never hardcode privacy values
- Embed hashtags in `title` field — no separate hashtag API exists
- Decouple upload (sync) from polling (async background) — `publish_id` is the handoff
- Encrypt credentials at rest from day one — TikTok tokens are long-lived (365d refresh)

---

## Sources

All sources are official TikTok developer documentation only.

- [Content Posting API Product Page](https://developers.tiktok.com/products/content-posting-api/)
- [Content Posting API — Get Started](https://developers.tiktok.com/doc/content-posting-api-get-started)
- [Content Posting API — Upload Content Guide](https://developers.tiktok.com/doc/content-posting-api-get-started-upload-content)
- [Content Posting API — Direct Post Reference](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post)
- [Content Posting API — Initialize Video Upload Reference](https://developers.tiktok.com/doc/content-posting-api-reference-upload-video)
- [Content Posting API — Get Video Status Reference](https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status)
- [Content Posting API — Query Creator Info Reference](https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info)
- [Content Posting API — Media Transfer Guide](https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide)
- [Content Sharing Guidelines](https://developers.tiktok.com/doc/content-sharing-guidelines)
- [Login Kit Overview](https://developers.tiktok.com/doc/login-kit-overview)
- [Login Kit for Web](https://developers.tiktok.com/doc/login-kit-web)
- [OAuth User Access Token Management](https://developers.tiktok.com/doc/oauth-user-access-token-management)
- [Manage User Access Tokens (v2)](https://developers.tiktok.com/doc/login-kit-manage-user-access-tokens)
- [API Scopes Overview](https://developers.tiktok.com/doc/scopes-overview)
- [API Scopes Reference](https://developers.tiktok.com/doc/tiktok-api-scopes)
- [API v2 Rate Limits](https://developers.tiktok.com/doc/tiktok-api-v2-rate-limit)
- [API v2 Error Handling](https://developers.tiktok.com/doc/tiktok-api-v2-error-handling)
