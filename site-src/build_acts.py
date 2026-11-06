#!/usr/bin/env python3
"""Build /site/<slug>/ activity pages from Activity.dc.html (uses build_site.py)."""
import subprocess, sys, os, re, json, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
SRC, SITE, BASE = sys.argv[1], sys.argv[2], sys.argv[3].rstrip('/') + '/'
I18N = json.load(open(os.path.join(HERE, 'i18n.json'), encoding='utf-8'))
tmp = tempfile.mkdtemp()
subprocess.run([sys.executable, os.path.join(HERE, 'build_site.py'), SRC, tmp, BASE], check=True, stdout=subprocess.DEVNULL)
js = open(os.path.join(tmp, 'app.js'), encoding='utf-8').read()
for n in ('counter', 'phone', 'printer'):
    js = js.replace('"img/%s.webp"' % n, '"../img/%s.webp"' % n)
open(os.path.join(SITE, 'act.js'), 'w', encoding='utf-8').write(js)
head = open(os.path.join(tmp, 'index.html'), encoding='utf-8').read()
PAGES = {
 'cafe': ('برنامج كاسة للقهوة وصالون الشاي', 'كاسة للقهوة: الإكسبريس بضغطة، وكل وردية بحسابها، والكريدي للحرفاء. ابتداءً من 1 دينار في النهار.'),
 'snack': ('برنامج كاسة للسناك والأكل السريع', 'كاسة للسناك، الملاوي، الكسكروت والشاورما: الطلب في ضغطتين، رقم كبير على التيكي، والربح على كل منتج. ابتداءً من 1 دينار في النهار.'),
 'pizzeria': ('برنامج كاسة للبيتزيريا', 'كاسة للبيتزيريا: الحجم يبدّل السوم والوصفة وحدو، والإضافات بسومها. ابتداءً من 1 دينار في النهار.'),
 'restaurant': ('برنامج كاسة للمطعم', 'كاسة للمطعم: الملاحظات للكوجينة، الخدّامة والمرتبات، المصاريف والربح الصافي. ابتداءً من 1 دينار في النهار.'),
 'boulangerie': ('برنامج كاسة للمخبزة والحلويات', 'كاسة للمخبزة والباتيسري: بيع الصباح بضغطة، والوصفات وتكلفة كل منتج. ابتداءً من 1 دينار في النهار.'),
 'kiosque': ('برنامج كاسة للكشك والمغازة', 'كاسة للكشك والعطّار: البيع بالبحث بالإسم، المخزون بالحبة، والكريدي بلاصة الكرني. ابتداءً من 1 دينار في النهار.'),
}
for slug, (title, desc) in PAGES.items():
    h = head
    h = re.sub(r'<title>.*?</title>', '<title>%s — SYN0X POS</title>' % title, h, flags=re.S)
    h = re.sub(r'<meta name="description" content=".*?">', '<meta name="description" content="%s">' % desc, h)
    h = re.sub(r'<meta property="og:description" content=".*?">', '<meta property="og:description" content="%s">' % desc, h)
    h = re.sub(r'<meta property="og:title" content=".*?">', '<meta property="og:title" content="%s — SYN0X POS">' % title, h)
    url = BASE + slug + '/'
    h = h.replace('<link rel="canonical" href="%s">' % BASE, '<link rel="canonical" href="%s">' % url)
    h = h.replace('<meta property="og:url" content="%s">' % BASE, '<meta property="og:url" content="%s">' % url)
    h = h.replace('href="favicon.svg"', 'href="../favicon.svg"').replace('href="icon-180.png"', 'href="../icon-180.png"')
    h = h.replace('src="vendor/', 'src="../vendor/')
    h = h.replace('<script src="app.js"></script>', '<script>window.SX_PROPS={act:"%s"}</script>\n<script src="../act.js"></script>' % slug)
    os.makedirs(os.path.join(SITE, slug), exist_ok=True)
    open(os.path.join(SITE, slug, 'index.html'), 'w', encoding='utf-8').write(h)
print('pages', len(PAGES))
