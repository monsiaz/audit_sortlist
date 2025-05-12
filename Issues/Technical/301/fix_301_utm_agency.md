# Fix outbound links on agency pages (301 issue)

## Description
On `/agency/` pages, outbound links to agency websites include UTM tracking (`utm_source`, `utm_medium`, `utm_campaign`). However, the current construction of `utm_campaign` (which encodes the full Sortlist URL) causes unnecessary 301 redirects, even when the target site is accessible.

## Recommendation
1. Keep UTM tracking, but replace the value of `utm_campaign` with the **slug** of the agency only (e.g. `datakudo`).
2. Always use the target domain in **lowercase** and **HTTPS**.
3. No longer encode the full Sortlist URL in `utm_campaign`.

### Recommended format:
```html
<a href="https://datakudo.com?utm_source=sortlist&utm_medium=profile&utm_campaign=datakudo">
```

## Offenders
- Button with full UTM in href:
  ```html
  <a class="btn" href="https://datakudo.com?utm_source=sortlist&utm_medium=profile&utm_campaign=https%3A%2F%2Fwww.sortlist.com%2Fagency%2Fperformanze" target="_blank">https://datakudo.com</a>
  ```
  ![Agency page UTM button](../../../Crawl/Capture/bouton_utm_agency.png)
  *Example of a button on an agency page with problematic UTM parameters*

- Obfuscated link with `rel` in base64:
  ```html
  <span class="btn" data-testid="openWebsite" rel="aHR0cHM6Ly9kYXRha3Vkby5jb20/dXRtX3NvdXJjZT1zb3J0bGlzdCZ1dG1fbWVkaXVtPXByb2ZpbGUmdXRtX2NhbXBhaWduPWh0dHBzJTNBJTJGJTJGd3d3LnNvcnRsaXN0LmNvbSUyRmFnZW5jeSUyRnBlcmZvcm1hbnpl">
    Open website
  </span>
  ```
  ![UTM button details](../../../Crawl/Capture/bouton_utm_details.png)
  *Details of the generated UTM link in the button*

### Table of Offending Links

| Type | Sortlist Agency URL | Outbound Link | HTTP Code | HTTP Status | Target | rel | Context | Selector | Comment |
|------|---------------------|--------------|-----------|-------------|--------|-----|---------|----------|---------|
| Hyperlien | https://www.sortlist.com/agency/mailander-srl | https://www.mailander.it/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/sic-marketing-solutions | https://sic-marketing.com/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/thorit-gmbh | https://www.thorit.de/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/jmr-digital-marketing | https://jmr-digital.com/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/plans-pixels | https://www.plansandpixels.nl/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/marcommit | https://www.marcommit.nl/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/pow-ideas | https://powideas.com/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/zigt-media | http://www.zigt.be/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/blend-snc | https://www.blendcomunicazione.it/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/umbau | http://www.umbau.be/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/la-superboite | http://www.lasuperboite.be/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/wowlab | http://www.wowlab.be/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/les-enchanteurs | https://www.lesenchanteurs.fr/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/trends-digital | http://www.trendsdigital.com/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/our-own-brand | https://ourownbrand.co/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/caracal-studio | http://www.caracal.agency/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |
| Hyperlien | https://www.sortlist.com/agency/immagina-communication | https://www.immaginacommunication.it/?utm_source=sortlist&utm_medium=profile&utm_campaign= | 301 | Moved Permanently | _blank | noopener | Absolu | //body/div/main/div/div[2]/div/div/div/div/div[7]/div/div[2]/div/div/div[2]/a | HTML |

