# Sources — covered, missing, and worth adding

A living audit of where job postings come from. "Free" means no paid API/proxy.

## ✅ Covered now

| Source | Type | How it's covered | Reliability |
|---|---|---|---|
| **Greenhouse** | ATS | Official public JSON per company | High |
| **Lever** | ATS | Official public JSON per company | High |
| **Ashby** | ATS | Official public JSON per company | High |
| **Personio** | ATS | Official public XML per company (big in DE) | High |
| **Workday** | ATS | Public cxs JSON per company (Mastercard, PayPal) | High |
| **Arbeitsagentur** | Board | Free official REST API (Germany's largest DB) | High |
| **Indeed** | Board | JobSpy (keyword + location search) | Medium |
| **Google Jobs** | Aggregator | JobSpy — also powers the `company_sweep` | Medium |
| **LinkedIn** | Board | JobSpy (enabled; rate-limits, may break) | Low–Med |
| **Amazon** | Company | Native public search API (off by default) | High |

**How the company list is used:** ATS/Workday feeds pull *all* roles from the
companies you list. Indeed, Google Jobs, LinkedIn and Arbeitsagentur are
*general* keyword searches, so they also surface roles at companies **not** on
your list. The `company_sweep` adds targeted Google-Jobs queries for named
companies that lack a clean feed.

## 🟡 Worth adding (free) — ask and I'll wire them in

| Source | Why | Effort |
|---|---|---|
| **SmartRecruiters** | Public API; used by Bosch, McDonald's, many EU corps | Easy |
| **Recruitee** | Public API; common in NL/DE startups | Easy |
| **Workable** | Public API/feed; common at SMBs | Easy |
| **Teamtailor** | Public feed; common in Nordics/DE | Easy |
| **RemoteOK / Remotive** | Free JSON APIs; remote-first roles | Easy |
| **EURES** | Official EU job-mobility portal API | Medium |
| **More Workday companies** | e.g. Visa (needs its site path found once) | Low each |

## 🔴 Missing / hard

| Source | Status |
|---|---|
| **StepStone** | Dominant in DE, but Akamai bot-protected → paid scraper only (~$1/1k) |
| **Xing** | DACH network; paid scraper only |
| **Glassdoor** | Anti-bot blocked (TLS fingerprinting) |
| **SuccessFactors (SAP)** | Used by Siemens/Allianz/BMW; per-tenant, often gated |
| **Oracle Recruiting (Amex)** | Amex's ATS; per-tenant, awkward — use Arbeitsagentur/sweep instead |
| **iCIMS / Taleo** | Legacy big-corp ATSs; gated |
| **Custom career sites** | PagoNxt, Check24, Revolut, Klarna, epay — no clean feed; caught via Google/LinkedIn sweep, or watch with changedetection.io |

## Notes on specific companies from the list

- **Mastercard, PayPal** → Workday feeds (added).
- **Amex** → Oracle Recruiting Cloud (not Workday) → covered via sweep + Arbeitsagentur.
- **KPMG (Germany)** → SeamlessHiring / TalentSoft (not Workday) → covered via sweep + Arbeitsagentur.
- **Adyen, N26, Stripe, Pliant, Westwing, Scalable, finway, FlixBus, FreeNow, Wise, SumUp, GoCardless, Binance** → clean ATS feeds (added).
- **PagoNxt, Revolut, Trade Republic, Klarna, Skrill, Paysafe, Check24, epay, Visa** → custom/other ATS → covered via Google-Jobs `company_sweep`.
