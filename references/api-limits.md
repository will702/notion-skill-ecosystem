# API limits and retry rules

Verified against https://developers.notion.com/reference/request-limits.md and the append-children docs (fetched 2026-11-09). The community figure "2 nesting levels" is confirmed; the other community numbers were re-checked against the official page.

## Size limits
| Item | Limit |
|---|---|
| `text.content` in a rich text object | 2,000 characters |
| `text.link.url`, any URL | 2,000 characters |
| `equation.expression` | 1,000 characters |
| Any array of blocks or rich text objects in one request | 100 elements |
| Request payload | 1,000 block elements and 500 KB overall |
| Nesting inside one append-children request | 2 levels |
| Multi-select options / relations / people per request | 100 each (relations can hold more; the limit is per request) |
| Email, phone | 200 characters |
| File upload on free plan | single_part only, up to 5 MB |
| Free workspace with more than one member | 1,000 lifetime blocks (single-member free and paid workspaces are unlimited) |

## Rate limits
| Scope | Limit |
|---|---|
| Per connection, Business and Enterprise | 600 requests/min (about 10/s) |
| Per connection, other plans | 180 requests/min (about 3/s) |
| Data source query | about 3 requests/s per connection |
| Workspace-wide | shared budget across connections |

## Retry rules
- Retry **429** and **529** always (except a 429 with `rate_limit_reason: public_api_request_blocked`). Honor `Retry-After` (integer seconds), then exponential backoff with jitter, with a retry cap.
- Retry **500, 502, 503, 504** only for idempotent requests (GET, DELETE). **Do not blindly retry POST or PATCH after a 5xx**: an append-children or page-create that actually succeeded would be duplicated. Instead re-read the target and compare before retrying.
- Queue outgoing requests so one job cannot consume the whole budget.
- Split work: pages with more than 100 blocks are appended in chunks of at most 100; long text runs are split below 2,000 characters.
- Pagination: pass `start_cursor` while `has_more` is true; `page_size` max 100.

## Local findings
- Run `ntn` with stdin closed (`< /dev/null`), otherwise background or scripted runs can hang.
- 502 responses from `api.notion.com` do occur transiently; for non-idempotent calls verify before retrying (see above).
