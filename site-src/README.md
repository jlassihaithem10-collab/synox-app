# Source of the SYN0X site (/site/)

- `Main.dc.html`: the page as designed in the Claude canvas "موقع SYN0X POS".
- `build_site.py`: converts it to the static page in `../site/` (React UMD, images, FR/EN translation runtime).
  `python3 build_site.py Main.dc.html ../site https://jlassihaithem10-collab.github.io/synox-app/site/`
  (needs `vendor/` React files already in `../site/vendor/`, and `i18n.json` next to the script).
- `i18n_extract.py`: lists every Arabic string of the page. `i18n_tr.py`: FR/EN translations in the same order; rebuild `i18n.json` after any text change.
