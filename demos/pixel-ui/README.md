# Pixel UI consumer demo

Use Python 3.10+ and the repository's Pillow requirement to rebuild from the maintained recipes:

```sh
python tools/build_consumer_demo.py --force
python -m http.server 8765 --bind 127.0.0.1 --directory demos/pixel-ui
```

Open `http://127.0.0.1:8765/` in a browser. The static demo has no npm build step, browser automation dependency or external runtime requests. The server is local; stop it with Ctrl+C. Opening `index.html` directly is not supported because the page fetches local JSON/assets and verifies hashes.

- Run, Loop and Export Map use actual PNG atlas cells, with consumer text rendered at native size and enlarged with nearest-neighbor scaling. Export Map is deliberately disabled. Tab/Shift+Tab, Enter and Space use native HTML button behavior.
- Scale changes 1×/2×/3×. Night/Paper changes the surrounding background. The six-state gallery is a reference; the live controls implement real hover, focus, press, selection and disabled behavior.
- Baseline/Revised loads separate frozen asset directories. The initial64px button has a30px text reservation. Revised96px has62px. The page measures actual glyph bounds with the loaded Silkscreen Regular font; use the checks panel to confirm whether labels fit. The baseline is retained as the integration-failure example, not the default production candidate.
- Change `demo.json`, rebuild, then reload. The builder regenerates PNG, editable JSON and content-bound layout together. Image content hashes in the manifest are checked before use, avoiding accidental old-PNG/new-layout mixtures. It does not promise crash-safe multi-file publication.

Sources are `recipes/buttons.py`, `courier128.py`, `icons.py` and `_common.py`. `assets/manifest.json` records recipe hashes, parameters and generated asset hashes. The consumer uses `layout.json` and reserved rectangles in `context.json`; it does not hand-copy atlas UV/state order into CSS.

The renderer/Skill still depends only on Python/Pillow. This browser example is repository-only, separate from the frozen rc.3 Skill ZIP, three external rc.2 trials, mod resources and installed stable Skill. No Minecraft font or in-game acceptance is claimed. The bundled font supports the Latin demo labels, not a Chinese-font acceptance claim.

Project code/art are MIT. Unmodified Silkscreen Regular is copyright The Silkscreen Project Authors and is distributed under **SIL Open Font License1.1**, retained at [fonts/OFL.txt](fonts/OFL.txt). [fonts/source.json](fonts/source.json) records the original Google Fonts files, Git blob IDs and SHA-256. The font retains its original name; do not relicense it as MIT.

The page's checks describe actual geometry/font loading and interaction state. They do not rank beauty or establish general model productivity. See the [P3 findings and screenshots](../../docs/consumer-ui-report.md), with a [detailed Chinese report](../../docs/consumer-ui-report.zh-CN.md).
