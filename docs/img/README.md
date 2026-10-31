# Course infographics

Rendered PNGs live here; their sources live in `src/`.

| Image | Teaches | Linked from |
|---|---|---|
| `01-sliding-line.png` | The sliding line of responsibility across on-prem, IaaS, PaaS and SaaS | Module 01, Part 1 |
| `03-resource-hierarchy.png` | The three resource hierarchies side by side, with policy attach points | Module 03, text diagram |
| `14-aws-policy-evaluation.png` | How AWS evaluates a request: grant vs limit, explicit deny wins | Module 14, AWS evaluation logic |
| `16-envelope-encryption.png` | Envelope encryption: DEK, KEK, wrap and unwrap | Module 16, envelope encryption |
| `22-detection-lifecycle.png` | The detection engineering lifecycle mapped to the intel cycle | Module 22, lifecycle |

To regenerate one:

```bash
pip install playwright && playwright install chromium
python3 docs/img/src/render.py docs/img/src/14-aws-policy-evaluation.json docs/img/14-aws-policy-evaluation.png
```

Fonts: Inter and DejaVu Sans Mono (`apt install fonts-inter fonts-dejavu` if missing).

Layouts: `steps` (an order things happen in, with an optional written-order strip), `cards` (a 2-column grid of building blocks or comparisons), `compare` (two side-by-side panels, wrong vs right), and `matrix` (rows × columns, e.g. who owns which layer). `render.py`'s docstring lists the spec keys. The renderer is shared across Brian's learning repos; keep one visual language.

Each `src/*.json` spec holds the text. Every fact must come from the module it's linked from, which carries the sources and verification date. If a module is re-verified and a fact changes, update the spec and re-render.
