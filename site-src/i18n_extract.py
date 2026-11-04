#!/usr/bin/env python3
"""List every Arabic string the SYN0X page shows (markup text, attributes, logic literals)."""
import re, sys, json
from html.parser import HTMLParser

src = open(sys.argv[1], encoding='utf-8').read()
tpl = re.search(r'</helmet>(.*?)</x-dc>', src, re.S).group(1)
logic = re.search(r'<script type="text/x-dc" data-dc-script[^>]*>(.*?)</script>', src, re.S).group(1)
AR = re.compile(r'[؀-ۿ]')
HOLE = re.compile(r'\{\{.*?\}\}')
ATTRS = {'alt', 'aria-label', 'placeholder', 'title', 'value'}
found = []


def add(t):
    t = t.strip() if not t.startswith('\n') else t
    if t and AR.search(t) and t not in found:
        found.append(t)


class P(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ATTRS and v:
                for part in HOLE.split(v):
                    add(part)

    def handle_data(self, d):
        for part in HOLE.split(re.sub(r'\s+', ' ', d)):
            add(part)


P(convert_charrefs=True).feed(tpl)
for m in re.finditer(r"'((?:[^'\\]|\\.)*)'", logic):
    lit = m.group(1).encode().decode('unicode_escape').encode('latin-1').decode('utf-8') if '\\' in m.group(1) else m.group(1)
    add(lit)
json.dump(found, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(found))
