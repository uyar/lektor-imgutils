# Copyright (C) 2023-2024 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-imgutils is released under the BSD license.
# Read the included LICENSE.txt file for details.

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Dict, List, Literal, Set, Tuple, Union

import typedload
from lektor.builder import Builder
from lektor.pluginsystem import Plugin
from lektor.reporter import reporter
from lxml import html
from lxml.cssselect import CSSSelector
from lxml.etree import _Element as Element
from PIL import Image, UnidentifiedImageError


from_html = html.fromstring
to_html = partial(html.tostring, encoding="unicode")


@dataclass
class ImageAttributes:
    width: Union[int, Literal["intrinsic"], None] = None
    height: Union[int, Literal["intrinsic"], None] = None
    loading: Union[Literal["eager", "lazy"], None] = None
    decoding: Union[Literal["sync", "async", "auto"], None] = None


class ImgUtilsPlugin(Plugin):
    name = "imgutils"
    description = "Image handling utilities."

    def on_setup_env(self, **extra) -> None:
        config = self.get_config()
        self.ops: Dict[CSSSelector, ImageAttributes] = {}
        for selector in config.sections():
            data = config.section_as_dict(selector)
            parsed = typedload.load(data, ImageAttributes, failonextra=True)
            self.ops[CSSSelector(selector)] = parsed
        self.image_data: Dict[Path, ImageAttributes] = {}
        self.skip_images: Set[Path] = set()

    def get_intrinsic_size(self, path: Path) -> Tuple[int, int]:
        data = self.image_data.get(path)
        if data is None:
            data = ImageAttributes()
            self.image_data[path] = data
        if (data.width is None) or (data.height is None):
            with Image.open(path) as image:
                data.width = image.width
                data.height = image.height
        return (data.width, data.height)

    def on_after_build_all(self, builder: Builder, **extra) -> None:
        reporter.report_generic("Starting image utilities")
        dst_root: str = builder.destination_path
        for page in Path(dst_root).glob("**/*.html"):
            content = page.read_text()
            tree = from_html(content)
            modified = False
            for selector, ops in self.ops.items():
                tags: List[Element] = selector(tree)
                for tag in tags:
                    atts = tag.attrib
                    src = atts.get("src")
                    if src is None:
                        continue
                    image_path = page.parent.joinpath(src).resolve()
                    if image_path in self.skip_images:
                        continue

                    if (ops.width is not None) and ("width" not in atts):
                        if ops.width == "intrinsic":
                            try:
                                width, _ = self.get_intrinsic_size(image_path)
                            except UnidentifiedImageError:
                                self.skip_images.add(image_path)
                                continue
                        else:
                            width = ops.width
                        atts["width"] = str(width)
                        modified = True

                    if (ops.height is not None) and ("height" not in atts):
                        if ops.height == "intrinsic":
                            try:
                                _, height = self.get_intrinsic_size(image_path)
                            except UnidentifiedImageError:
                                self.skip_images.add(image_path)
                                continue
                        else:
                            height = ops.height
                        atts["height"] = str(height)

                    if (ops.loading is not None) and ("loading" not in atts):
                        atts["loading"] = ops.loading
                        modified = True

                    if (ops.decoding is not None) and ("decoding" not in atts):
                        atts["decoding"] = ops.decoding
                        modified = True

            if modified:
                page.write_text(to_html(tree))
        reporter.report_generic("Finished image utilities")
