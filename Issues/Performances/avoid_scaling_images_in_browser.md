# Avoid scaling images in browser

## Description
While it's convenient to rely on CSS/browser resizing for responsiveness, client-side image scaling hurts both CPU usage (especially on mobile devices) and page load performance. Users end up downloading extra kilobytes—or even megabytes—of data unnecessarily. To optimize LCP and overall SEO performance, generate and serve multiple image variants server-side and let your build or CDN deliver the best fit for each viewport and DPR.

## Recommendation
1. During your image build process (or in your image CDN), generate multiple widths and DPR versions for each asset (e.g., 320, 480, 768, 1024, 1440 px).
2. Use `<img srcset>` or Next.js's `next/image` `sizes` and `loader` config to deliver the correct size.
3. Audit your bundler/CDN rules to ensure no images exceed the max displayed size by more than 100 px.

## Offenders

URL -> https://www.sortlist.com/i/digital-marketing/paris-fr 

- `https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fblizzard.svg&w=1920&q=75`
- `https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Fyale.svg&w=1920&q=75`
- `https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Flinkedin.svg&w=1920&q=75`
- `https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Flogos%2Fcompanies%2Ffarm.svg&w=1920&q=75`
- `https://ca.slack-edge.com/T02GTPALY-U063FNX813P-e7429429745f-192`
- `https://www.sortlist.com/_next/image?url=https%3A%2F%2Fsortlist-public-ui-manual-upload-production.s3.eu-west-1.amazonaws.com%2Ficons%2Fsocial%2Flinkedin.svg&w=32&q=75`

