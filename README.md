# Electronics Storage Shelves

CAD models, renders, and build documents for a mobile electronics workbench setup:

- **Four shelf units** (identical; 30 W × 15 D × 29½ H in, on casters) built from `Plans for shelves.pdf`.
- **Two soldering tool totes** (identical; 12½ L × 8 D × 9 H in) built from `Plans for tool totes.pdf`, with a 1 in round dowel handle in place of the plan's rectangular handle.
- **Two back-to-back workbench tables** (72 × 30 in tops at 36 in) and a **layout model** placing the four shelf units under the tables with both totes on one lower shelf.

Models are written in [build123d](https://github.com/gumyr/build123d). Dimensions are parameterized in inches and built in millimetres. Values not fixed by the plans or by measurement are marked as estimates in the scripts and viewer notes.

## Folder layout

```
.
├── Plans for shelves.pdf             Source plan: shelf unit
├── Plans for tool totes.pdf          Source plan: tool tote
├── Electronics storage shelves.png   Reference image: shelf unit
├── Electronics Tool Tote.png         Reference image: tool tote
├── scripts/
│   ├── shelf_unit.py                 Model: one shelf unit
│   ├── tote.py                       Model: one tool tote
│   ├── workbench_tables.py           Model: two back-to-back tables
│   ├── workbench_layout.py           Model: 4 shelves + 2 totes under the tables (reuses the three models above)
│   ├── build_viewer.py               -> output/shelf_viewer.html
│   ├── verify_export.py              -> output/shelf_unit.step (with re-import checks)
│   ├── build_tote.py                 -> output/tote.step, output/tote_viewer.html
│   ├── build_tables.py               -> output/workbench_tables.step, output/workbench_tables_viewer.html
│   ├── build_layout.py               -> output/workbench_layout.step, output/workbench_layout_viewer.html
│   ├── render.py                     -> output/shelf_unit_front.png, output/shelf_unit_rear.png
│   ├── render_layout.py              -> output/images/01_*.png … 07_*.png
│   └── *_template.html               three.js viewer templates filled in by the build scripts
└── output/
    ├── *.step                        STEP assemblies (named solids)
    ├── *_viewer.html                 Self-contained 3D viewers (geometry embedded; published as artifacts)
    ├── cut_list.html                 Shelf & tote cut list (published as an artifact)
    ├── *.png                         Single-model renders
    └── images/                       Layout renders
```

## Regenerating outputs

### Requirements

- Python 3 with **build123d** (all build/verify/render scripts), **numpy** (`build_viewer.py`, `build_tote.py`, `build_tables.py`, `render.py`), and **VTK** (`render.py`, `render_layout.py`).
- The viewer pages load three.js 0.128.0 and Google Fonts from CDNs when opened, so viewing needs a network connection.

The model files (`shelf_unit.py`, `tote.py`, `workbench_tables.py`) call `show(...)`, which is provided by an interactive build123d session. The build scripts load them with `runpy` and inject a no-op `show`, so run the build scripts rather than the model files directly.

### Order

Run from the repository root:

```sh
python scripts/build_viewer.py     # shelf viewer page
python scripts/verify_export.py    # shelf STEP + checks
python scripts/build_tote.py       # tote STEP + viewer (prints overlap/screw checks)
python scripts/build_tables.py     # tables STEP + viewer
python scripts/build_layout.py     # layout STEP + viewer
python scripts/render.py           # shelf front/rear PNGs (VTK, off-screen)
python scripts/render_layout.py    # layout PNGs in output/images/ (VTK, off-screen)
```

Dependencies between steps:

- `build_layout.py` reuses geometry already embedded in `shelf_viewer.html`, `workbench_tables_viewer.html` and `tote_viewer.html`, so run `build_viewer.py`, `build_tables.py` and `build_tote.py` first whenever one of those models changes.
- `render_layout.py` takes part colours from `shelf_viewer.html` and `tote_viewer.html`, so rebuild those first too.
- `render.py` and `verify_export.py` hard-code the project's absolute path; edit `PROJECT` at the top of each if the repo moves. `render.py` also writes diagnostic crops to `/tmp`.

Not produced by any script in `scripts/`: `output/images/tote.png`, `output/workbench_tables.png`, `output/workbench_layout.png`, and `output/cut_list.html`. Edit or regenerate those by hand.

## Published artifacts

Each published page on claude.ai has exactly one local source file in `output/`. The published copies were compared against these files and match byte-for-byte (apart from the document wrapper the artifact service adds at publish time), so there is no separate `artifacts/` copy. To update a page, regenerate or edit the local file and republish it to the same URL.

| Artifact | URL | Local file |
|---|---|---|
| Shelf Unit Viewer | https://claude.ai/artifact/H76V1PcBFt5gnFJNytedxa | `output/shelf_viewer.html` |
| Soldering Tool Tote Viewer | https://claude.ai/artifact/7GBuV2i5KmS1qSqgUQUWvx | `output/tote_viewer.html` |
| Workbench Tables Viewer | https://claude.ai/artifact/2MpPxdgmLp37QoKHx3xoaT | `output/workbench_tables_viewer.html` |
| Workbench Shelf Layout | https://claude.ai/artifact/5uunoo4kGy1DtfMKYB4sMs | `output/workbench_layout_viewer.html` |
| Shelf & Tote Cut List | https://claude.ai/artifact/BGmmrpCPsUdUBnbS9oLbmt | `output/cut_list.html` |

## Repository notes

- Line endings are normalized to LF (`.gitattributes`). PDFs, images and STEP files are stored as binary; viewer pages are text but have diffs suppressed because each embeds megabytes of geometry on one line.
- Git LFS is not used: the largest file (`output/workbench_layout.step`) is about 8 MB.
