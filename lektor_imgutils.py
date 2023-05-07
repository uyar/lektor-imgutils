from pathlib import Path

import pillow_avif
from bs4 import BeautifulSoup
from jxlpy import JXLImagePlugin
from lektor.pluginsystem import Plugin
from lektor.reporter import reporter
from PIL import Image


class ImgUtilsPlugin(Plugin):
    name = "imgutils"
    description = "Image handling utilities."

    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        conf = self.get_config()
        self.sections = {s: conf.section_as_dict(s) for s in conf.sections()}
        self.images = {}

    def is_enabled(self, extra_flags):
        return bool(extra_flags.get("imgutils"))

    def on_after_build_all(self, builder, **extra):
        extra_flags = getattr(
            builder, "extra_flags", getattr(builder, "build_flags", None)
        )
        if not self.is_enabled(extra_flags):
            return
        reporter.report_generic("Starting image utilities")
        for page in Path(builder.destination_path).glob("**/*.html"):
            content = page.read_text()
            soup = BeautifulSoup(content, "html.parser")
            modified = False

            added_attrs = {}
            for section, options in self.sections.items():
                selector = options["_selector"]
                generate = options.get("_generate", [])
                for tag in soup.select(selector):
                    img_file = page.parent.joinpath(tag["src"]).resolve()
                    if img_file not in self.images:
                        self.images[img_file] = {}
                    if tag not in added_attrs:
                        added_attrs[tag] = {}

                    sized = ("width" in tag.attrs) or ("height" in tag.attrs)
                    if ("size" in generate) and (not sized):
                        img_data = self.images[img_file]
                        if ("width" not in img_data) or ("height" not in img_data):
                            with Image.open(img_file) as img:
                                img_data["width"] = img.width
                                img_data["height"] = img.height
                        added_attrs[tag]["width"] = img_data["width"]
                        added_attrs[tag]["height"] = img_data["height"]

                    for attr, val in options.items():
                        if (attr[0] != "_") and (attr not in tag.attrs):
                            added_attrs[tag][attr] = val

            lines = content.splitlines()
            for tag in soup.find_all("img"):
                img_file = page.parent.joinpath(tag["src"]).resolve()
                added = added_attrs.get(tag, {})
                if len(added) > 0:
                    line_no = tag.sourceline - 1
                    line = lines[line_no]
                    pos = line.index("i", tag.sourcepos) + 3
                    assert line[pos - 3:pos] == "img", line
                    assert line[pos].isspace(), line

                    add_str = " ".join(f'{k}="{v}"' for k, v in added.items())
                    lines[line_no] = line[:pos] + " " + add_str + line[pos:]
                    modified = True

            if modified:
                page.write_text('\n'.join(lines))
        reporter.report_generic("Finished image utilities")
