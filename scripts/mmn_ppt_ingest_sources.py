#!/usr/bin/env python3
"""Convert Word/PPT/PDF/Excel inputs to Markdown with MarkItDown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from markitdown import MarkItDown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="Source files: docx, pptx, pdf, xlsx, csv, html, etc.")
    parser.add_argument("--outdir", default="output/ppt-agent/markdown", help="Markdown output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    md = MarkItDown(enable_plugins=False)
    manifest = []

    for item in args.inputs:
        source = Path(item).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        result = md.convert(str(source))
        target = outdir / f"{source.stem}.md"
        text = getattr(result, "text_content", None) or getattr(result, "markdown", "")
        target.write_text(text, encoding="utf-8")
        manifest.append({"source": str(source), "markdown": str(target), "chars": len(text)})

    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"converted": len(manifest), "outdir": str(outdir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
