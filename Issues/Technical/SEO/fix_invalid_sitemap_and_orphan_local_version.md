# Fix invalid sitemap structure + unlinked localized pages

## Description  
The sitemap at [`https://www.sortlist.com/sitemaps/2/sitemap.xml.gz`](https://www.sortlist.com/sitemaps/2/sitemap.xml.gz) is **invalid** and **not readable** by search engines due to both structural and semantic issues.

### Sample of current raw content
```
https://www.sortlist.com/es/3d2025-05-07T23:00:34+00:00daily0.5
https://www.sortlist.com/3d-animation2025-05-07T23:00:34+00:00daily0.5
https://www.sortlist.com/nl/3d-bureaus2025-05-07T23:00:34+00:00daily0.5
...
```

This format **lacks valid XML tags**, so Googlebot can't parse it.

## Recommendation

1.  ### Generate proper XML structure  
    Each URL entry should look like:

    ```xml
    <url>
      <loc>https://www.sortlist.com/fr/3d-design</loc>
      <lastmod>2025-05-07T23:00:34+00:00</lastmod>
      <changefreq>daily</changefreq>
      <priority>0.5</priority>
    </url>
    ```

    Wrap everything in a root tag:

    ```xml
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      ...entries...
    </urlset>
    ```

    Also make sure:
    - The `.gz` file returns correct headers: `Content-Type: application/gzip`
    - Decompressed XML is valid and UTF-8 encoded

2.  ### Localized pages in sitemap, but not linked anywhere  
    Many URLs are localized (e.g. `/fr/`, `/es/`, `/de/`) and declared in the sitemap, but **not linked in the internal linking** or language selector. These pages are basically orphaned.

    If these versions are meant to be indexed, then:
    - Add language links to the language selector/footer
    - Declare proper `<link rel="alternate" hreflang="x">` tags in the HTML head

    Otherwise, don't include them in the sitemap.

### XML sitemap example 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.sortlist.com/es/3d</loc>
    <lastmod>2025-05-07T23:00:34+00:00</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://www.sortlist.com/3d-animation</loc>
    <lastmod>2025-05-07T23:00:34+00:00</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
```

Fixing this will help ensure:
- Proper crawl coverage
- No indexation of orphaned content
- Better control over international SEO signals
