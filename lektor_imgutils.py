# Copyright (C) 2023-2024 H. Turgut Uyar <uyar@tekir.org>
#
# lektor-imgutils is released under the BSD license.
# Read the included LICENSE.txt file for details.

from pathlib import Path

from bs4 import BeautifulSoup
from lektor.pluginsystem import Plugin
from lektor.reporter import reporter
from PIL import Image, UnidentifiedImageError


IMG_ATTRS = {"decoding", "loading"}


class ImgUtilsPlugin(Plugin):
    name = "imgutils"
    description = "Image handling utilities."

    def on_setup_env(self, **extra):
        self.ops = {}
        config = self.get_config()
        for section in config.sections():
            selector = config.pop(f"{section}.selector")
            if selector not in self.ops:
                self.ops[selector] = {}

            set_size = config.get_bool(f"{section}.set_size", None)
            if set_size is not None:
                self.ops[selector]["set_size"] = set_size
                config.pop(f"{section}.set_size")

            options = config.section_as_dict(section)
            for attr, value in options.items():
                if attr in IMG_ATTRS:
                    self.ops[selector][attr] = value

        self.images = {}
        self.skip_images = set()

    def get_size(self, image_path):
        image_data = self.images[image_path]
        if ("width" not in image_data) or ("height" not in image_data):
            image = None
            try:
                image = Image.open(image_path)
                image_data["width"] = image.width
                image_data["height"] = image.height
            finally:
                if image is not None:
                    image.close()
        return {"width": image_data["width"], "height": image_data["height"]}

    def on_after_build_all(self, builder, **extra):
        reporter.report_generic("Starting image utilities")

        for page in Path(builder.destination_path).glob("**/*.html"):
            content = page.read_text()
            soup = BeautifulSoup(content, "html.parser")

            added_attrs = {}
            for selector, ops in self.ops.items():
                set_size = ops.pop("set_size", False)
                for tag in soup.select(selector):
                    image_path = page.parent.joinpath(tag["src"]).resolve()
                    if image_path in self.skip_images:
                        continue
                    if image_path not in self.images:
                        self.images[image_path] = {}
                    if tag not in added_attrs:
                        added_attrs[tag] = {}

                    if set_size and ("width" not in tag.attrs) and ("height" not in tag.attrs):
                        try:
                            size_attrs = self.get_size(image_path)
                            if len(size_attrs) > 0:
                                added_attrs[tag].update(size_attrs)
                        except UnidentifiedImageError:
                            self.skip_images.add(image_path)
                            del self.images[image_path]
                            continue

                    for attr, value in ops.items():
                        if attr not in tag.attrs:
                            added_attrs[tag][attr] = value

            modified = False
            lines = content.splitlines()
            for tag in soup.find_all("img"):
                added = added_attrs.get(tag, {})
                if len(added) > 0:
                    line_no = tag.sourceline - 1
                    line = lines[line_no]
                    pos = line.index("img", tag.sourcepos) + 3
                    add_str = " ".join(f'{k}="{v}"' for k, v in added.items())
                    lines[line_no] = line[:pos] + " " + add_str + line[pos:]
                    modified = True

            if modified:
                page.write_text('\n'.join(lines))

        reporter.report_generic("Finished image utilities")
