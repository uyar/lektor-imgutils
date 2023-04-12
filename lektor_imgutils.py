from pathlib import Path

from bs4 import BeautifulSoup
from lektor.pluginsystem import Plugin
# from lektor.reporter import reporter
from PIL import Image


class ImgUtilsPlugin(Plugin):
    name = "imgutils"
    description = "Image handling utilities."

    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        config = self.get_config()

        self.sections = {}
        for section in config.sections():
            self.sections[section] = {
                "selector": config.get(f"{section}.selector"),
                "size": config.get_bool(f"{section}.size", False),
                "loading": config.get(f"{section}.loading"),
                "decoding": config.get(f"{section}.decoding"),
            }

        self.images = {}

    def on_after_build_all(self, builder, **extra):
        # reporter.report_generic("image utilities started")
        for page in Path(builder.destination_path).glob("**/*.html"):
            content = page.read_text()
            soup = BeautifulSoup(content, "html.parser")
            modified = False

            added_attrs = {}
            for options in self.sections.values():
                for tag in soup.select(options["selector"]):
                    img_file = page.parent.joinpath(tag["src"]).resolve()
                    if img_file not in self.images:
                        self.images[img_file] = {}
                    if tag not in added_attrs:
                        added_attrs[tag] = {}

                    sized = ("width" in tag.attrs) or ("height" in tag.attrs)
                    if options["size"] and (not sized):
                        img_data = self.images[img_file]
                        if ("width" not in img_data) or ("height" not in img_data):
                            with Image.open(img_file) as img:
                                img_data["width"] = img.width
                                img_data["height"] = img.height
                        added_attrs[tag]["width"] = img_data["width"]
                        added_attrs[tag]["height"] = img_data["height"]

                    loading = options.get("loading")
                    if (loading is not None) and ("loading" not in tag.attrs):
                        added_attrs[tag]["loading"] = loading

                    decoding = options.get("decoding")
                    if (decoding is not None) and ("decoding" not in tag.attrs):
                        added_attrs[tag]["decoding"] = decoding

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
        # reporter.report_generic("image utilities finished")
