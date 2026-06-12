# Raven Control Starter Site

Simple static HTML/CSS starter for `ravencontrol.com`.

## Files

- `index.html`
- `style.css`
- `ask-raven.html`
- `ask-raven.js`
- `backend/` for the Render API service

## Preview locally

Open `index.html` in a browser, or serve the folder with a simple static server.

Example:

```bash
cd ravencontrol-site
python3 -m http.server 8080
```

Then visit: <http://localhost:8080>

## Next likely edits

- replace placeholder copy with your real offer
- change contact email
- add logo / favicon
- add pricing, portfolio, or intake form
- deploy to Cloudflare Pages, Netlify, GitHub Pages, or your own server

## Backend

Deploy `backend/` to Render as a Python Web Service. See
`backend/README.md`.
