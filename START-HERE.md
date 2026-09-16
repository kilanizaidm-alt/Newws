# News Translation Classroom

A public English–Arabic classroom website with daily source-linked lessons,
15–20 contextual glossary entries, and translation practice. Students need no
AI account. The code uses Python's standard library and a static website; no
subscription, database, custom domain or paid search service is required.

## What is ready

- Responsive reading view, Arabic right-to-left layout, vocabulary search and
  translation practice that stays in the current browser tab.
- Daily news collection from BBC World and UN News, with UN Arabic reporting
  available for same-event language comparisons.
- Two bounded Gemini requests per attempted update: drafting and a separate
  AI review. No automatic retries, fallback paid model, or paid search tool.
- A 30-edition archive and preservation of the last successful edition on error.
- A GitHub Actions workflow that publishes only the `web` directory.

The bundled preview is fictional practice material, visibly labelled as such.
The live Gemini calls have not been tested without your API key. A separate AI
review is not human verification. Stories without a matching Arabic reference
are explicitly labelled as not externally verified.

## Finish the one-time setup

1. Create a **public** GitHub repository named `news-translation-classroom` in
   your own account at https://github.com/new. Use `main` as the default branch.
   Initialize it with a README. If the ChatGPT GitHub connection uses selected
   repositories, grant it access to this repository. Return its link to the
   assistant, which can then upload the prepared files. Alternatively upload
   this package's contents yourself, including `.github/workflows/daily.yml`.
   Files should be at the repository root, not inside an extra enclosing folder.
2. In that repository, open **Settings → Pages** and set **Source** to
   **GitHub Actions**. If needed, under **Settings → Actions → General**, allow
   the workflow and permit read/write workflow access so editions can be saved.
3. In Google AI Studio, create an API key in an eligible project that remains
   on the **free tier with billing disabled**: https://aistudio.google.com/apikey.
   Do not enter payment details or upgrade the project for this setup.
4. In GitHub, open **Settings → Secrets and variables → Actions → Secrets →
   New repository secret**. Name it `GEMINI_API_KEY` and paste the key there.
   Never put it in a public file, website, screenshot, issue or chat message.
5. Under the adjacent **Variables** tab, add `FREE_TIER_CONFIRMED` with value
   `true`, only after checking the API project's free-tier status. This is your
   confirmation; the updater cannot inspect or enforce Google's billing tier.
6. Open **Actions → Daily classroom edition → Run workflow**. Once it succeeds,
   find the actual website link under **Settings → Pages** and share it.

The schedule requests one update at **06:23 UTC daily**. GitHub may delay or
drop a scheduled run; this is not a guaranteed exact delivery time. In public
repositories, scheduled workflows may be disabled after 60 days with no
repository activity. Inspect Actions if updates stop. The website shows the
actual edition date and flags editions more than 48 hours old.

Your earlier ChatGPT daily briefing is separate and still enabled. This GitHub
workflow does not rely on it or on a ChatGPT subscription.

## Keep the operating cost at zero

- Keep the repository public and use its included `github.io` address.
- Keep `ubuntu-latest` standard runners; do not select larger paid runners.
- The site artifact lasts one day. No dependency cache or large media is stored.
- Keep the Gemini API project on its free tier with billing disabled. Model
  availability and quotas vary by account and region and can change. If the free
  model is unavailable or a limit is reached, stop and retain the last edition;
  do not switch on billing. Failure is preferable to an unexpected charge.
- The updater currently targets `gemini-3-flash-preview`, whose text input and
  output are listed as free-tier eligible as checked on 15 September 2026. Check
  current availability before activation. There is no paid search grounding.
- This design cannot promise that third-party free plans will remain unchanged.
- Only public news text is sent to Google; do not add student submissions or
  personal data. Google's free-tier terms may permit use to improve products.

## Sources and translation quality

The updater collects recent reports (72-hour maximum, prioritizing 24 hours),
then drafts five original summaries and idiomatic Arabic model translations.
Its second AI pass checks factual support, attribution, modality, proper names,
and terminology. It removes Arabic references that do not cover the same event.
Programmatic checks reject invented source IDs, incomplete output and glossary
examples absent from the English summaries. These checks cannot establish
perfect factual or translation accuracy; a teacher should review work used in
formal assessment. No result is labelled human-certified.

The public page links readers to original reporting. It does not republish full
articles, images or publisher translations. Source coverage is limited to the
configured publishers; it is not an exhaustive global news service.

## Local preview and tests

From the project folder:

```sh
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 --directory web
```

Open http://localhost:8000. No key is needed for the fictional preview.
Without both activation settings, `python3 scripts/update_news.py` exits without
making AI requests or changing the lesson. Review the workflow's actual results
after activation; a passing local test is not an end-to-end API or hosting test.

## Official service references

- GitHub Pages availability: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- Actions free standard runners and storage: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini API: https://ai.google.dev/api/generate-content
- Scheduled workflow limitations: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
