#!/usr/bin/env python3
"""Builds the Leon AII site from src/.

  index.html            full standalone page (deploy this folder to Netlify as is)
  build/leon-aii.html   the same page as a fragment, for publishing as a Claude Artifact
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500"
         "&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Hebrew:wght@400;500;600"
         "&family=Noto+Sans+Hebrew:wdth,wght@62.5,800&family=Sofia+Sans+Extra+Condensed:wght@700;800;900&display=swap")
DESC = ("Leon AII: one engineer and a team of AI. Websites, ads, an AI receptionist on WhatsApp, automation, "
        "video, drawings and estimates for businesses in Israel and worldwide. Hebrew, English, Russian.")
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
        "%3Crect width='64' height='64' fill='%231238C8'/%3E%3Cpath d='M14 14v36h16M38 14v36M50 14v36' "
        "stroke='%23fff' stroke-width='7' fill='none'/%3E%3Cpath d='M50 14v36' stroke='%23FF5A1F' stroke-width='7'/%3E%3C/svg%3E")

def read(name):
    return (SRC / name).read_text(encoding="utf-8")

css, body = read("style.css"), read("body.html")
js = "\n".join(read(n) for n in ("i18n.js", "catalog.js", "app.js"))
assert "</script" not in js.lower()

core = f"<style>\n{css}</style>\n{body}\n<script>\n{js}</script>\n"

fragment = (
    "<title>Leon AII</title>\n"
    '<meta name="claude:viewport-fit-sides" content="cover">\n'
    f'<link rel="stylesheet" href="{FONTS}">\n' + core)

full = f"""<!doctype html>
<html lang="ru" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Leon AII</title>
<meta name="description" content="{DESC}">
<meta property="og:title" content="Leon AII — one engineer, a team of AI">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://leonaii.com/">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#1238C8">
<link rel="icon" href="{ICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
</head>
<body>
{core}</body>
</html>
"""

(ROOT / "build").mkdir(exist_ok=True)
(ROOT / "build" / "leon-aii.html").write_text(fragment, encoding="utf-8")
(ROOT / "index.html").write_text(full, encoding="utf-8")
print(f"index.html {len(full)//1024} KB · build/leon-aii.html {len(fragment)//1024} KB")
