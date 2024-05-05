# Copyright (C) 2023-2024 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-imgutils is released under the BSD license.
# Read the included LICENSE.txt file for details.

from functools import partial
from pathlib import Path

from lektor.pluginsystem import Plugin
from lektor.reporter import reporter
from lxml import html
from lxml.cssselect import CSSSelector
from PIL import Image, UnidentifiedImageError


IMG_ATTRS = {"decoding", "loading"}


from_html = html.fromstring
to_html = partial(html.tostring, encoding="unicode")


class ImgUtilsPlugin(Plugin):
    name = "imgutils"
    description = "Image handling utilities."

    def on_setup_env(self, **extra):
        config = self.get_config()

        self.ops = {}
        for section in config.sections():
            selector_expr = config.pop(f"{section}.selector")
            selector = CSSSelector(selector_expr)
            if selector not in self.ops:
                self.ops[selector] = {}

            set_size = config.get_bool(f"{section}.set_size", None)
            if set_size is not None:
                self.ops[selector]["set_size"] = set_size
                config.pop(f"{section}.set_size")

            options = config.section_as_dict(section)
            for attr, value in options.items():
                if attr not in IMG_ATTRS:
                    raise ValueError(f"Unknown image property: {attr}")
                self.ops[selector][attr] = value

        self.image_data = {}
        self.skip_images = set()

    def get_size(self, image_path):
        image_data = self.image_data[image_path]
        if ("width" not in image_data) or ("height" not in image_data):
            image = None
            try:
                image = Image.open(image_path)
                image_data["width"] = str(image.width)
                image_data["height"] = str(image.height)
            finally:
                if image is not None:
                    image.close()
        return {"width": image_data["width"], "height": image_data["height"]}

    def on_after_build_all(self, builder, **extra):
        reporter.report_generic("Starting image utilities")
        for page in Path(builder.destination_path).glob("**/*.html"):
            content = page.read_text()
            tree = from_html(content)
            modified = False
            for selector, ops in self.ops.items():
                set_size = ops.pop("set_size", False)
                for tag in selector(tree):
                    src = tag.attrib["src"]
                    image_path = page.parent.joinpath(src).resolve()
                    if image_path in self.skip_images:
                        continue
                    if image_path not in self.image_data:
                        self.image_data[image_path] = {}
                    if set_size and ("width" not in tag.attrib) and \
                        ("height" not in tag.attrib):
                        try:
                            size_attrs = self.get_size(image_path)
                            if len(size_attrs) > 0:
                                tag.attrib.update(size_attrs)
                                modified = True
                        except UnidentifiedImageError:
                            self.skip_images.add(image_path)
                            del self.image_data[image_path]
                            continue
                    for attr, value in ops.items():
                        if attr not in tag.attrib:
                            tag.attrib[attr] = value
            if modified:
                page.write_text(to_html(tree))
        reporter.report_generic("Finished image utilities")
