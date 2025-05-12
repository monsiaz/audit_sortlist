# Improvement proposal: landing page content via AI and aggregated data

## Description

The objective of this proposal is to significantly improve the quality, relevance, and SEO performance of Sortlist's landing page content (main SEO text and FAQ sections). This would be achieved by adopting an Artificial Intelligence (AI) assisted content generation approach, fueled by rich, contextual, and aggregated data specific to each landing page.

## Problem / opportunity

**Current problem:**
The content on some landing pages can sometimes lack specificity, appear generic, or fail to fully leverage the wealth of available data regarding providers (agencies, etc.) and services featured on these pages. This can limit user engagement and SEO effectiveness.

**Opportunity:**
There is a major opportunity to create content that is:
-   **More relevant and specific:** Aligning with precise user expectations.
-   **Better informed by data:** Increasing its credibility and value.
-   **Optimized for search intent:** Improving search engine rankings.
-   **Scalable:** Allowing for the coverage of a large number of landing pages with high-quality content.

## Proposed solution / methodology

We propose using advanced AI models (e.g., OpenAI's GPT models) to dynamically generate the main SEO text and distinct FAQ sections for each landing page.

**The pillars of this approach are:**

### AI data input

The quality of AI-generated content is directly proportional to the quality and richness of the data provided. For each landing page, the AI would be fed:

-   **Aggregated provider data (via JSON or API):**
    *   Calculated statistics for providers listed on the page: average ratings, typical team sizes, observed project budget ranges, most common services, average number of projects, main industries served, etc.
    *   Sentiment analysis and key takeaways from client reviews.
    *   Concrete and anonymized examples of completed projects.
-   **Specific market/service context:**
    *   Textual data on local market trends or the relevant sector (similar to the `egytp_market_resume.txt` file used in our example).
-   **For FAQs only: previously generated main SEO content:**
    *   To ensure FAQs provide real added value and are not redundant, the main SEO text of the landing page (generated in a previous step) will be provided to the AI as context.

### Prompt engineering

Carefully crafted prompts are essential to guide the AI. They must instruct the AI to:
-   Focus exclusively on the landing page's subject (e.g., SEO agencies in Egypt).
-   Explicitly integrate and cite the provided data to support its claims.
-   Avoid generalities and prioritize specificity.
-   Adopt an appropriate tone and style for the target audience (B2B decision-makers, etc.).
-   Adhere to the desired HTML structure (e.g., start directly with `<h2>`, `<h3>`/`<p>` format for FAQs).
-   Achieve an indicative text length (e.g., 1000-1200 words for the main text).

## Expected benefits

-   **Improved content quality and relevance:** More specific, informative, and directly useful texts.
-   **Search intent optimization:** Better content alignment with user queries, leading to improved SEO ranking.
-   **Increased user engagement:** Rich and credible content builds trust and encourages action.
-   **Better overall SEO performance:** High-quality content favored by search engine algorithms.
-   **Content creation scalability:** Ability to produce high-quality content for a large volume of landing pages.
-   **Enriched user experience:** Users find more precise answers and deeper information.

## Implementation example and reference script

A Python script, located at `Crawl/Scripts/content_generation_example.py`, has been developed to demonstrate the feasibility and effectiveness of this approach.

**Example script functionality:**
1.  **Loading source data:**
    *   It loads structured data about agencies from a JSON file (e.g., `sortlist-analyzer/data/seo_agencies_egypt.json`).
    *   It loads contextual market information from a text file (e.g., `sortlist-analyzer/data/egytp_market_resume.txt`).
2.  **Data processing and aggregation:**
    *   The script calculates various statistics (averages, minimums, maximums, distributions).
    *   It formats project lists and client review excerpts.
3.  **Detailed prompt construction:**
    *   Based on the processed data, it builds specific and highly directive prompts for the AI.
4.  **Interaction with OpenAI API:**
    *   It sends these prompts to a GPT model (configurable, currently `o3-2025-04-16` in the script's latest version) to generate:
        *   A main SEO text.
        *   A distinct and complementary FAQ section.
5.  **Basic multilingual management:**
    *   The script includes logic to generate content in English and then translate it into other specified languages (via the OpenAI API).
6.  **Saving results:**
    *   The generated HTML content is saved into separate files (e.g., `main_seo_egypt_en.html`, `faq_seo_egypt_en.html`).

This script serves as a concrete illustration of the proposed methodology.

### Generated content examples

Below are snippets from the output generated by the `Crawl/Scripts/content_generation_example.py` script when processing data for SEO agencies in Egypt. These demonstrate the type of main SEO text and FAQ section the script can produce.

**Main SEO text example (`main_seo_egypt_en.html`):**

```html
<h2>Egypt's SEO landscape: data-driven overview</h2>
<p>The SEO market in Egypt sits at the intersection of rapid digital adoption and a maturing agency ecosystem. Egypt Digital Market Insights records <strong>96.3 million internet users in early 2025, equal to 81.9 percent penetration</strong>. Add to that <strong>116 million active mobile connections—99 percent of the population</strong>—and the business case for high-performance search visibility becomes clear: virtually every potential customer is reachable online, most of them via mobile search.</p>

<h3>Search behaviour in a mobile-first environment</h3>
<p>Mobile connectivity shapes both user expectations and SEO strategy. With median mobile download speeds at <strong>24.17 Mbps</strong> and fixed-line speeds averaging <strong>76.67 Mbps</strong> (Egypt Digital Market Insights), on-page performance—Core Web Vitals, site architecture, and schema—directly affects rankings and conversions. Agencies therefore emphasise technical SEO and page-speed optimisation: projects such as <em>SEO Overhaul for E-commerce Client</em> (Agency G, 2024) and <em>SEO Overhaul for E-commerce Client</em> (Agency H, 2021) each included comprehensive technical audits to ensure fast, mobile-friendly experiences for B2C shoppers.</p>
```
(Full file: [../../Crawl/Scripts/main_seo_egypt_en.html](../../Crawl/Scripts/main_seo_egypt_en.html))

**FAQ section example (`faq_seo_egypt_en.html`):**

```html
<h3>Do I really need to optimise for both Arabic and English keywords in Egypt?</h3>
<p>In most verticals—especially e-commerce, healthcare and SaaS—the answer is "yes." Roughly 70 % of consumer queries on Egyptian SERPs are in Arabic, while English dominates B2B and tech research. Agencies that ranked highest in client reviews (4.6 – 4.95/5) routinely deploy bilingual content clusters, pair <code>hreflang</code> tags with right-to-left (RTL) styling fixes, and localise meta data rather than just translate it. The payoff is twofold: Arabic pages capture volume, and English pages earn backlinks from regional tech press, lifting overall domain authority.</p>

<h3>What timeline should I expect before organic traffic or bookings start to climb?</h3>
<p>Based on 20 documented projects, agencies follow a three-phase cadence:</p>
<ul>
<li><strong>Weeks 1-4 – Diagnostic & Quick Wins:</strong> Technical audit, Core Web Vitals fixes, Google Business Profile clean-up. Local clinics in the "Medical Practice" series saw map views rise within the first 30 days.</li>
</ul>
```
(Full file: [../../Crawl/Scripts/faq_seo_egypt_en.html](../../Crawl/Scripts/faq_seo_egypt_en.html))

## Key considerations and recommendations

-   **Data richness is paramount:** AI performance is intrinsically linked to the quality, quantity, and structuring of the provided data. **The richer and more precise the input data (variables in the prompts), the more qualitative and relevant the generated content will be.** It is therefore crucial to invest in collecting and preparing this data.
-   **Multilingual capability:** The approach is compatible with a multilingual strategy. The example script shows how translation can be managed. For optimal results, providing already translated input data (if possible) or ensuring the quality of post-generation translation is important. This obviously only applies if a landing page version exists for the target language.
-   **Prompt engineering and iteration:** Prompt formulation is an art that requires iteration. It will be necessary to continuously adjust prompts based on the results obtained to refine content quality and relevance.
-   **API costs:** Using AI model APIs incurs costs that will depend on the volume of content to be generated and the complexity of the models used.
-   **Human validation:** Although AI can generate high-quality content, human validation (proofreading, minor adjustments) is recommended, at least initially, to ensure perfect alignment with the brand and strategic objectives.

## Suggested next steps

1.  Identify a pilot set of landing pages to test this approach.
2.  Define and collect/structure the necessary data sources for these pilot pages.
3.  Adapt and refine the `content_generation_example.py` script for these use cases.
4.  Analyze the results (content quality, SEO performance, engagement) and iterate.
5.  Plan for a broader rollout if the results are conclusive. 