# Fix SEO for paginated pages: canonical, noindex, and optimization

## Description
Paginated result pages (e.g., `/i/design/paris-fr?page=2`) currently use a canonical tag pointing to the root (page 1) and are set to `noindex,follow`. This means:
- Only the first page is indexed and can rank in Google.
- All paginated pages (page 2, 3, etc.) are excluded from the index and do not pass their full link equity.
- This can waste crawl budget and dilute the SEO value of deep content and agency listings.

## Recommendation
1. **Use self-referencing canonical tags** on paginated pages (e.g., page 2 canonical = page 2 URL).
2. **Remove `noindex`**: Use `index,follow` on paginated pages so Google can index and rank them if relevant.
3. **De-optimize paginated pages**: Use a variable like `@page_number@` to generate less-optimized titles and meta descriptions for paginated pages. Example:
   - **Title:** `Page @page_number@ – Agencies in @Location@ | Sortlist`
   - **Meta description:** `Discover more agencies in @Location@. This is page @page_number@ of our listings.`

4. **Limit pagination depth**:
   - Limit to 100 pages for main category landings (e.g., France). If pagination > 100, redirect pages > 100 to the main landing.
   - Limit to 50 pages for city landings. If pagination > 50, redirect pages > 50 to the main landing.
   - Inflate the number of results per page (e.g., 101 per page) to reduce the number of paginated URLs.
5. **Pagination links UX**:
   - On landings, only show links to page 2 and the last page (not all pages).
   - For deep paginations, show links to every 10th page (10, 20, 30, ... last).

## Example of the current issue
- **URL:** https://www.sortlist.com/i/design/paris-fr?page=2
- **Canonical:** https://www.sortlist.com/i/design/paris-fr
- **Meta robots:** noindex,follow
- **Title:** The 10 Best Design Agencies in Paris - 2025 Reviews
- **Meta description:** Find & hire the best Design Agencies in Paris. Here are the best ones listed just for you based on verified client reviews.

## Why fix?
- Allows paginated content to be indexed and rank for long-tail queries
- Preserves link equity and improves SEO for deep content
- Reduces crawl budget waste
- Avoids duplicate content and cannibalization

## Why this approach? (Expert opinion)
Over years of SEO consulting and real-world testing, I have directly compared both approaches: blocking paginated pages (noindex/canonical to root) vs. allowing their indexation with self-canonical. Here's why I strongly recommend the latter:

- **Real-world results:** My PDF analysis (see link below) demonstrates clear SEO gains when paginated pages are indexed, especially for long-tail and deep content queries. This is not just theory—it's based on real data from a similar project.
- **Quick win:** Switching to self-canonical and index,follow is a low-effort, high-impact change. It can unlock hundreds or thousands of new entry points for organic traffic with minimal dev work.
- **Long-tail leverage:** Paginated pages often surface niche, less competitive queries that main landings cannot capture. This brings incremental, high-quality traffic.
- **Link equity flow:** Allowing indexation ensures that link equity is distributed throughout the paginated set, not just concentrated on page 1. This benefits all listed agencies or items.
- **Crawl efficiency:** Googlebot can discover and index more content naturally, without being artificially blocked or forced to recrawl page 1 repeatedly.
- **User experience:** Users landing on deep pages from Google are more likely to find exactly what they want, reducing bounce rates and improving engagement.

> **I understand the concerns about duplicate content, crawl budget, and index bloat. However, with proper de-optimization and pagination limits, these risks are minimal compared to the SEO upside.**

## Resources & previous analysis
- [Pagination V2 analysis PDF](../../../sortlist-analyzer/data/Pagination%20V2.pdf) *(includes real-case study and data supporting this recommendation)*

## Example of improved implementation
```html
<!-- On page 3 of /i/design/paris-fr -->
<link rel="canonical" href="https://www.sortlist.com/i/design/paris-fr?page=3" />
<meta name="robots" content="index,follow" />
<title>Page 3 – Agencies in Paris | Sortlist</title>
<meta name="description" content="Discover more agencies in Paris. This is page 3 of our listings.">
<h1>Agencies in Paris (Page 3)</h1>