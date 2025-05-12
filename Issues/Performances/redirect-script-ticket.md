# Avoid Redirects on Script Assets

## Description

The page includes a JavaScript asset that is served via a **redirect**, introducing unnecessary latency in loading — especially critical on mobile devices.

> A redirect adds an extra HTTP request before the browser receives the final asset. This slows down page rendering and increases Time to Interactive (TTI).

## Affected URL

Redirected script:
- https://www.sortlist.com/cdn-cgi/challenge-platform/scripts/jsd/main.js

## Suggested Fix

- **Use the final, resolved URL directly** if possible, to eliminate the extra round trip caused by the redirect.
- If the redirect is managed by Cloudflare or a security system, consider adjusting the routing or rewriting configuration to serve the asset directly.

## Why It Matters

Redirects:
- Add latency, especially over mobile and high-latency networks.
- Increase DNS + TCP + TLS overhead.
- Are avoidable for static script resources.

---

This issue was identified from performance analysis of the following page:
https://www.sortlist.com/digital-marketing/united-states-us

Improving this will slightly reduce load times and eliminate avoidable delay from script redirection.
