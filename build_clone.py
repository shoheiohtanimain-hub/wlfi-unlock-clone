import re, base64, urllib.request, sys

BASE = "https://worldlibertyfinancial.com"
html = open("wlfi-unlock-raw.html", encoding="utf-8").read()

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read()

def datauri(content, mime):
    return f"data:{mime};base64," + base64.b64encode(content).decode()

MIMES = {".svg":"image/svg+xml",".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",
         ".webp":"image/webp",".gif":"image/gif",".woff2":"font/woff2",".woff":"font/font-woff"}

cache = {}
def get_data_uri(rel):
    if rel in cache: return cache[rel]
    path = rel.split("?")[0]
    ext = "." + path.rsplit(".",1)[-1].lower()
    mime = MIMES.get(ext, "application/octet-stream")
    content = fetch(BASE + rel)
    uri = datauri(content, mime)
    cache[rel] = uri
    print(f"inlined {rel} ({len(content)} bytes)")
    return uri

# 1. Inline the two stylesheets
css_links = re.findall(r'<link rel="stylesheet" href="([^"]+)"[^>]*/>', html)
css_parts = []
for href in css_links:
    css = fetch(BASE + href).decode("utf-8")
    # inline any url() assets inside css
    def css_url(m):
        u = m.group(1)
        if u.startswith("/_next") or u.startswith("/images"):
            return "url(" + get_data_uri(u) + ")"
        return m.group(0)
    css = re.sub(r'url\(([^)]+)\)', css_url, css)
    css_parts.append(f"/* {href} */\n{css}")
    html = html.replace(f'<link rel="stylesheet" href="{href}"[^>]*/>', "", regex=False) if False else re.sub(r'<link rel="stylesheet" href="' + re.escape(href) + r'"[^>]*/>', '', html)

style_block = "<style>\n" + "\n".join(css_parts) + "\n</style>"
html = html.replace("</head>", style_block + "\n</head>", 1)

# 2. Replace preload links with data (drop preloads)
html = re.sub(r'<link rel="preload"[^>]*/>', '', html)
html = re.sub(r'<link rel="preconnect"[^>]*/>', '', html)

# 3. Inline img/logo/number svgs and fonts referenced in HTML
for rel in set(re.findall(r'(?:src|href)="(/(?:_next|images)/[^"]+?\.(?:svg|png|jpg|jpeg|webp|gif|woff2?)(?:\?[^"]*)?)"', html)):
    uri = get_data_uri(rel)
    html = html.replace('="' + rel + '"', '="' + uri + '"')

# 4. Strip Next.js script tags (static snapshot)
html = re.sub(r'<script[^>]*src="[^"]*"[^>]*>\s*</script>', '', html)
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)

# 5. Inline favicon links (drop remote icon links)
html = re.sub(r'<link rel="(?:apple-touch-icon|icon|manifest)"[^>]*/>', '', html)

header = """<!--
  Static single-file clone of https://worldlibertyfinancial.com/unlock
  Generated for educational/personal use. All rights to original content
  belong to World Liberty Financial.
-->
"""
open("index.html","w",encoding="utf-8").write(header + html)
print("WROTE index.html", len(html), "chars")
