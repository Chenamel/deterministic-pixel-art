# Source and fixture provenance

The toolkit was extracted and optimized from the user's `llm-pixel-art` scripts. The complete source project and the separate optimization/evaluation archive were preserved locally; neither is required by a clone of this repository.

The repository includes 86 frozen fixture files: 18 original Python scripts, 25 matching project PNG resources, and 43 captured original PNG outputs. These support compatibility comparisons and selected benchmarks. Original relative project names are retained as fixture identifiers, not live output destinations. The historical scripts are test inputs; use `src/pixel_art.py` as the executable entrypoint.

`baselines/manifest.json` records SHA-256 values for every included snapshot and captured output. Git preserves their exact bytes, including original line endings. Unrelated mod metadata, resources, virtual environments, local paths, and the full 96-file preservation inventory are not included.

The new examples demonstrate generic palettes and geometry plus optional Minecraft-inspired GUI conventions. There are no bundled game executables or third-party Python packages. Project code and fixtures are distributed under the root MIT license, selected by the repository owner. Pillow and PyYAML retain their own licenses as separately installed dependencies.

`measurements/metrics.json` and `first-pass-metrics.json` preserve the original local optimization measurements. They are historical evidence, not CI performance thresholds. The Chinese report describes that original run; fresh runs write their own evidence to ignored `evaluation/`.
