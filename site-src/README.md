# Source of the SYN0X site (/site/)

- `Main.dc.html`: the page as designed in the Claude canvas "موقع SYN0X POS".
- `build_site.py`: converts it to the static page in `../site/` (React UMD, images, FR/EN translation runtime).
  `python3 build_site.py Main.dc.html ../site https://jlassihaithem10-collab.github.io/synox-app/site/`
  (needs `vendor/` React files already in `../site/vendor/`, and `i18n.json` next to the script).
- `i18n.json`: the FR/EN dictionary (Arabic text → fr/en). `i18n_extract.py` lists every Arabic string of the page; add any missing one to `i18n.json` before rebuilding. (`i18n_tr.py` was the first batch, kept for reference.)
