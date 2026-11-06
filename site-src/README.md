# Source of the SYN0X site (/site/)

- `Main.dc.html`: the page as designed in the Claude canvas "موقع SYN0X POS".
- `build_site.py`: converts it to the static page in `../site/` (React UMD, images, FR/EN translation runtime).
  `python3 build_site.py Main.dc.html ../site https://jlassihaithem10-collab.github.io/synox-app/site/`
  (needs `vendor/` React files already in `../site/vendor/`, and `i18n.json` next to the script).
- `i18n.json`: the FR/EN dictionary (Arabic text → fr/en). `i18n_extract.py` lists every Arabic string of the page; add any missing one to `i18n.json` before rebuilding. (`i18n_tr.py` was the first batch, kept for reference.)

## Activity pages (/site/<slug>/)
- `Activity.dc.html`: one template; the activity data (6 groups) lives in its script (`DATA`).
- `build_acts.py Activity.dc.html ../site <base-url>`: builds `../site/act.js` and one `index.html` per slug (cafe, snack, pizzeria, restaurant, boulangerie, kiosque) with its own title/description. New activity = new entry in `DATA` + `PAGES` in build_acts.py + translations in i18n.json.
