# Hosting

The app is a **fully static site**: no backend, no database, no login, and hash
routing (so no SPA rewrite rules). The built output is ~872 KB across ~30 files.
That puts it far inside every free tier, so hosting should cost nothing.

```
dist/  872 KB total
  index.html                    0.4 KB
  assets/index-*.js           349 KB  (113 KB gzipped)
  assets/index-*.css           23 KB  (4.5 KB gzipped)
  catalog/**                  500 KB  (8 models + validation + analysis)
```

## Recommendation

**GitHub Pages**, because the repo is going open source on GitHub anyway. No new
accounts, no vendor to evaluate, free at this size indefinitely, and the deploy
workflow is already in `.github/workflows/deploy.yml`.

Move to **Cloudflare Pages** if you later want a Neo4j-controlled hostname such
as `ontoforge.neo4j.com` plus per-PR preview deploys.

## Options compared

| Host | Cost | Notes |
|---|---|---|
| **GitHub Pages** | free | Free Pages requires a **public** repo. 1 GB site / ~100 GB month bandwidth. Custom domain + TLS free. Workflow already written. |
| **Cloudflare Pages** | free | Unlimited bandwidth, per-branch preview deploys, custom domain free, commercial use permitted. Build: `npm ci && npm run build` in `apps/web`, output `apps/web/dist`. |
| **Netlify** | free | ~100 GB month bandwidth, ~300 build min/month. Fine, but no advantage here. |
| **Vercel** | avoid | The free Hobby tier is for non-commercial use; a Neo4j-published tool would need a paid plan. |
| **S3 + CloudFront** | ~$1–2/mo | Most control, most setup. Only worth it if it must live in Neo4j AWS. |

Free-tier limits move — verify current numbers before committing to one.

## Deploy to GitHub Pages

1. Create the repo and push:

   ```bash
   gh repo create <org>/ontoforge --public --source=. --remote=origin --push
   ```

2. Turn on Pages with GitHub Actions as the source:

   ```bash
   gh api -X POST repos/<org>/ontoforge/pages -f build_type=workflow
   ```

   (Or: Settings → Pages → Source → GitHub Actions.)

3. Push to `main`, or run the workflow manually:

   ```bash
   gh workflow run "Deploy web app"
   ```

The site lands at `https://<org>.github.io/ontoforge/`. `vite.config.ts` sets
`base: "./"`, so the subpath works without configuration — this is verified, not
assumed: the build was served from a `/ontoforge/` subdirectory and the catalog
fetch, assets and hash routes all resolved correctly.

### Custom domain

```bash
echo ontoforge.neo4j.com > apps/web/public/CNAME
```

Then add a `CNAME` DNS record pointing at `<org>.github.io` and enable
*Enforce HTTPS* in Settings → Pages.

## Deploy to Cloudflare Pages

Connect the repo in the Cloudflare dashboard and set:

| Setting | Value |
|---|---|
| Build command | `npm ci && npm run build` |
| Build output directory | `apps/web/dist` |
| Root directory | `apps/web` |
| Node version | `22` |

No other configuration is needed.

## What CI does

- `ci.yml` on every push and PR: runs the golden-file regression (the nine
  hand-built models are the specification), validates the committed catalog
  bundle, checks the bundle is **in sync** with the profiles, and typechecks and
  builds the web app.
- `deploy.yml` on pushes touching `apps/web/**`: builds and publishes to Pages.

Deploy needs only Node, because the catalog bundle is committed. That keeps it
around 30 seconds and avoids downloading a 137 MB FIBO clone on every deploy.

## Refreshing the catalog

Currently a **local** step, not automated — `ontoforge fetch` and
`sources.yaml` are not built yet (roadmap phase 5). To refresh after a standard
publishes a new version:

```bash
# 1. fetch sources manually (see each profile's `source:` block for the URL)
# 2. re-ingest -> IR + analysis
PYTHONPATH=packages/core:packages/ingest python -c "..."   # see catalog/ir
# 3. re-export the bundle and commit
PYTHONPATH=packages/core python -m ontoforge.cli export
```

CI fails if the committed bundle drifts from the profiles, so a stale catalog
cannot ship silently.

## Before making the repo public

Read `NOTICE.md`. FIBO, AUTO and IOF are verified MIT. GS1, EPCIS, IDMP and FHIR
carry no licence declaration that could be verified from their distributions, and
the catalog ships models derived from them. To publish a narrower catalog:

```bash
PYTHONPATH=packages/core python -m ontoforge.cli export --exclude gs1 epcis idmp fhir
```
