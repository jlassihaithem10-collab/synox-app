#!/usr/bin/env python3
"""Convert the SYN0X canvas artboard (.dc.html) into a standalone static page (React UMD)."""
import json, re, sys, shutil, os
from html.parser import HTMLParser

SRC, OUT, BASE_URL = sys.argv[1], sys.argv[2], sys.argv[3]
IMG_MAP = {
    '/_blob/e949dd649c41e8758f459be862b6301f': 'img/counter.webp',
    '/_blob/e99d1fc6ee8a3e2f28b4734b3f71af02': 'img/phone.webp',
    '/_blob/ea007f97c52607d51eca1435239fc866': 'img/printer.webp',
}
src = open(SRC, encoding='utf-8').read()
for k, v in IMG_MAP.items():
    src = src.replace(k, v)

helmet = re.search(r'<helmet>(.*?)</helmet>', src, re.S).group(1)
tpl = re.search(r'</helmet>(.*?)</x-dc>', src, re.S).group(1)
script_m = re.search(r'<script type="text/x-dc" data-dc-script data-props=\'(.*?)\'>(.*?)</script>', src, re.S)
props_decl = json.loads(script_m.group(1).replace('&amp;', '&').replace('&#39;', "'"))
logic = script_m.group(2)
defaults = {k: v.get('default') for k, v in props_decl.items() if not k.startswith('$')}

VOID = {'img', 'input', 'br', 'hr', 'meta', 'link', 'source'}


class Node:
    def __init__(self, tag, attrs):
        self.tag, self.attrs, self.children = tag, attrs, []


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root', [])
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


p = P()
p.feed(tpl)

# svg/camel attribute names as the parser lowercases them
CASE = {'viewbox': 'viewBox', 'patternunits': 'patternUnits', 'onclick': 'onClick', 'oninput': 'onInput',
        'onchange': 'onChange', 'class': 'className', 'for': 'htmlFor', 'tabindex': 'tabIndex',
        'readonly': 'readOnly', 'maxlength': 'maxLength', 'autocomplete': 'autoComplete'}
TAGCASE = {'lineargradient': 'linearGradient', 'radialgradient': 'radialGradient'}
HOLE = re.compile(r'\{\{\s*(.*?)\s*\}\}')


def expr(path):
    path = path.strip()
    if path in ('true', 'false', 'null'):
        return path
    if re.fullmatch(r'-?\d+(\.\d+)?', path):
        return path
    if re.fullmatch(r"'[^']*'", path):
        return path
    return 'g(s,' + json.dumps(path) + ')'


AR = re.compile(r'[\u0600-\u06FF]')


def lit(t, tr):
    return ('__tr(' + json.dumps(t) + ')') if (tr and AR.search(t)) else json.dumps(t)


def interp(val, tr=False):
    m = HOLE.fullmatch(val.strip())
    if m:
        return expr(m.group(1))
    parts, last = [], 0
    for m in HOLE.finditer(val):
        if m.start() > last:
            parts.append(lit(val[last:m.start()], tr))
        parts.append('str(' + expr(m.group(1)) + ')')
        last = m.end()
    if last < len(val):
        parts.append(lit(val[last:], tr))
    return '(' + '+'.join(parts) + ')' if parts else '""'


def attr_name(n):
    if n in CASE:
        return CASE[n]
    if n.startswith('aria-') or n.startswith('data-'):
        return n
    return re.sub(r'-([a-z])', lambda m: m.group(1).upper(), n)


def gen(node):
    if isinstance(node, str):
        if not node.strip():
            return None if '\n' in node or not node else json.dumps(' ')
        t = re.sub(r'\s+', ' ', node)
        return interp(t, True)
    if node.tag == 'sc-for':
        a = dict(node.attrs)
        body = gen_children(node)
        var = a['as']
        return ('(arr(' + interp(a['list']) + ')).map(function(it,i){var s0=s;return (function(s){return h(F,{key:i},' +
                body + ')})(ext(s0,' + json.dumps(var) + ',it,i))})')
    if node.tag == 'sc-if':
        a = dict(node.attrs)
        return '(' + interp(a['value']) + '?h(F,null,' + gen_children(node) + '):null)'
    tag = TAGCASE.get(node.tag, node.tag)
    props = []
    style = None
    is_input = tag in ('input', 'select', 'textarea')
    for k, v in node.attrs:
        if k.startswith('hint-'):
            continue
        v = v if v is not None else ''
        if k == 'style':
            style = 'st(' + interp(v) + ')'
            continue
        name = attr_name(k)
        if name == 'onInput' and is_input:
            name = 'onChange'
        if name in ('onChange',) and tag == 'select':
            pass
        props.append(json.dumps(name) + ':' + interp(v, k in ('alt', 'aria-label', 'placeholder', 'title', 'value')))
    if style:
        props.append('style:' + style)
    if tag == 'form':
        props.append('onSubmit:function(e){e.preventDefault()}')
    pr = '{' + ','.join(props) + '}' if props else 'null'
    if node.tag in VOID:
        return 'h(' + json.dumps(tag) + ',' + pr + ')'
    return 'h(' + json.dumps(tag) + ',' + pr + ',' + gen_children(node) + ')'


def gen_children(node):
    items = [x for x in (gen(c) for c in node.children) if x is not None]
    return ','.join(items) if items else 'null'


body_js = gen_children(p.root)
logic = re.sub(r"'((?:[^'\\\n]|\\.)*)'", lambda m: ("__tr('" + m.group(1) + "')") if AR.search(m.group(1)) and m.group(1) != 'تونسي' else m.group(0), logic)
I18N = json.load(open(os.path.join(os.path.dirname(__file__), 'i18n.json'), encoding='utf-8'))

runtime = r'''
(function(){
var h=React.createElement,F=React.Fragment;
var I18N=__I18N__;
var LANG=(function(){var q=(location.search.match(/[?&]lang=(ar|fr|en)/)||[])[1];try{if(q)localStorage.setItem('sx-lang',q);return q||localStorage.getItem('sx-lang')||'ar'}catch(e){return q||'ar'}})();
var TITLES={ar:document.title,fr:'SYN0X POS — La caisse intelligente des commerces tunisiens',en:'SYN0X POS — The smart till for Tunisian shops'};
function applyDoc(){document.documentElement.lang=LANG;document.documentElement.dir=LANG==='ar'?'rtl':'ltr';document.title=TITLES[LANG]||TITLES.ar}
function __tr(x){if(LANG==='ar'||typeof x!=='string')return x;var e=I18N[x];if(e)return e[LANG];var m=x.match(/^(\s*)([\s\S]*?)(\s*)$/);e=I18N[m[2]];return e?m[1]+e[LANG]+m[3]:x}
var ROOT=null;
window.SXSetLang=function(l){LANG=l;try{localStorage.setItem('sx-lang',l)}catch(e){}applyDoc();setTimeout(function(){ROOT.render(h(Component,Object.assign({key:l},DEF)))},0)};
function g(s,path){var parts=path.split('.');var v=(parts[0] in s.__loc)?s.__loc[parts[0]]:s.__v[parts[0]];for(var i=1;i<parts.length;i++){if(v==null)return v;v=v[parts[i]]}return v}
function ext(s,name,it,i){var loc=Object.assign({},s.__loc);loc[name]=it;loc.$index=i;return {__v:s.__v,__loc:loc}}
function arr(x){return Array.isArray(x)?x:[]}
function str(x){return x==null?'':String(x)}
var stCache={};
function st(str0){if(stCache[str0])return stCache[str0];var o={};str0.split(';').forEach(function(d){var k=d.indexOf(':');if(k<0)return;var p=d.slice(0,k).trim(),v=d.slice(k+1).trim();if(!p)return;if(p.indexOf('--')!==0){p=p.replace(/^-webkit-/,'Webkit-').replace(/-([a-z])/g,function(m,c){return c.toUpperCase()})}o[p]=v});stCache[str0]=o;return o}
function TPL(v){var s={__v:v,__loc:{}};return h(F,null,__BODY__)}
class DCLogic extends React.Component{render(){return TPL(this.renderVals())}}
__LOGIC__
var DEF=__DEFAULTS__;
applyDoc();ROOT=ReactDOM.createRoot(document.getElementById('root'));ROOT.render(h(Component,Object.assign({key:LANG},DEF)));
})();
'''.replace('__BODY__', body_js).replace('__LOGIC__', logic).replace('__DEFAULTS__', json.dumps(defaults, ensure_ascii=False)).replace('__I18N__', json.dumps(I18N, ensure_ascii=False))

# helmet: keep link + style; drop editor-only bits
helmet_html = helmet.strip()

title = 'SYN0X POS — الكاسة الذكية للمحلات التونسية'
desc = 'برنامج كاشير على التابلت ولا الـcaisse للسناك، الفاست فود، البيتزيريا، القهاوي، المطاعم والأكشاك. يخدم بلا إنترنت. ابتداءً من 1 دينار في النهار.'
og = BASE_URL.rstrip('/') + '/og.jpg'
page = f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#141518">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="canonical" href="{BASE_URL}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_TN">
<meta property="og:title" content="SYN0X POS — الكاسة الذكية، ابتداءً من 1 د في النهار">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE_URL}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{og}">
{helmet_html}
</head>
<body>
<div id="root"></div>
<noscript><p style="font-family:sans-serif;padding:24px">SYN0X POS — WhatsApp: +216 29 495 848</p></noscript>
<script src="vendor/react.production.min.js"></script>
<script src="vendor/react-dom.production.min.js"></script>
<script src="app.js"></script>
</body>
</html>
'''
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)
open(os.path.join(OUT, 'app.js'), 'w', encoding='utf-8').write(runtime)
print('ok', len(page), len(runtime))
