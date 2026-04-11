# Deploy Raven Control to Cloudflare Pages

## 1) Create a GitHub repository

In GitHub, create a new repo, for example:
- `ravencontrol-site`

Do not add a README there if uploading from this existing folder.

## 2) Set git identity locally (if needed)

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 3) Commit the site

```bash
cd /home/akeem/.openclaw/workspace/ravencontrol-site
git add .
git commit -m "Initial Raven Control site"
```

## 4) Connect to GitHub

Replace the URL below with your real repo URL:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ravencontrol-site.git
git push -u origin main
```

## 5) Create a Cloudflare Pages project

In Cloudflare:
- Go to **Workers & Pages**
- Click **Create application**
- Choose **Pages**
- Choose **Connect to Git**
- Select your GitHub repo

Use these settings:
- **Framework preset:** None
- **Build command:** leave blank
- **Build output directory:** /

## 6) Add custom domain

Add:
- `ravencontrol.com`
- optionally `www.ravencontrol.com`

Cloudflare will show the DNS records needed.
If DNS stays at GoDaddy, add the exact records there.

## Notes

This site is static HTML/CSS, so Cloudflare Pages is a very good fit.
