# Ineffective Cache Headers on Multiple Requests

## Description

Multiple requests have missing or poorly configured `Cache-Control` headers. This includes Sortlist `_next/image` requests, which are reloaded on every visit due to ineffective caching policies (e.g., `max-age=0`). These behaviors degrade performance and increase network usage.

The analysis presented here is based on a single example URL; however, the caching strategy and recommendations should be reviewed and applied across various asset types (images, scripts, stylesheets) and page templates throughout the site to ensure comprehensive performance improvements.

![Cache Headers Example](../../Crawl/Capture/header-cache.png)
*Above: Example of cache headers for a Sortlist asset, illustrating the current caching policy.*

## Affected URLs

### Sortlist-controlled URLs (caching fix recommended):
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fgsk.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fnew-balance.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fbbc.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fblizzard.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Festee-lauder.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Famazon.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fbosch.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fvelux.svg&w=1080&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Ficons%2Fsocial%2Flinkedin.svg&w=32&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Ficons%2Fflags%2Fcertified-flag-primary.svg&w=48&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Ficons%2Fflags%2Fverified-flag-primary.svg&w=48&q=75
- https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Ficons%2Fflags%2Ffeatured-flag-primary.svg&w=48&q=75

### Third-party URLs (outside our control):
- https://cdn.growthbook.io/sub/sdk-bhAm8EdUUvMX9303
- https://secure.leadforensics.com/Track/Capture.aspx?retType=js&trk_jshv=1&trk_uid=&trk_user=118936&trk_sw=1710&trk_sh=1107&trk_ref=&trk_tit=The%2010%20Best%20Digital%20Marketing%20Agencies%20in%20USA%20-%202025%20Reviews&trk_loc=https%3A%2F%2Fwww.sortlist.com%2Fdigital-marketing%2Funited-states-us&trk_agn=Netscape&trk_agv=Mozilla%2F5.0%20(Macintosh%3B%20Intel%20Mac%20OS%20X%2010_15_7)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F136.0.0.0%20Safari%2F537.36&trk_dom=www.sortlist.com&trk_cookie=NA&trk_culid=01JTT68KWTB1QN5JX3ABJ1K2AC
- https://a.usbrowserspeed.com/cs
- https://secure.leadforensics.com/apollo/capture

## Suggested fix (Only for Sortlist URLs)

Update your server or CDN configuration to apply long-term caching headers to static assets, such as:

```
Cache-Control: public, max-age=31536000, immutable
```

This ensures that versioned static content like images doesn't get reloaded on each visit.

## Notes on Third-party URLs

These external scripts and SDKs cannot be controlled directly. If needed, consider:
- Loading them asynchronously
- Auditing their necessity
- Deferring non-critical third-party scripts

Improving cache headers for Sortlist assets will reduce redundant downloads and improve load times across repeat visits.
