from pathlib import Path

from bs4 import BeautifulSoup
from lektor.pluginsystem import Plugin
# from lektor.reporter import reporter
from PIL import Image

IMG_DATA = {}


class ImgUtilsPlugin(Plugin):
    name = "lektor-imgutils"
    description = "Image handling utilities."

    def on_after_build_all(self, builder, **extra):
        # reporter.report_generic("image utilities started")
        for html_file in Path(builder.destination_path).glob("**/*.html"):
            modified = False
            content = html_file.read_text()
            lines = content.splitlines()
            soup = BeautifulSoup(content, "html.parser")
            for img_tag in soup.find_all("img"):
                img_attrs = img_tag.attrs
                img_file = html_file.parent.joinpath(img_tag["src"]).resolve()
                if ("width" not in img_attrs) and ("height" not in img_attrs):
                    img_data = IMG_DATA.get(img_file, {})
                    if len(img_data) == 0:
                        with Image.open(img_file) as img:
                            img_data["width"] = img.width
                            img_data["height"] = img.height
                        IMG_DATA[img_file] = img_data

                    line = lines[img_tag.sourceline - 1]
                    assert line[img_tag.sourcepos] == "<", line
                    start_pos = line.index("i")
                    assert line[start_pos:start_pos + 3] == "img", line
                    assert line[start_pos + 3].isspace(), line
                    new_attrs = 'width="%(width)s" height="%(height)s"' % img_data
                    new_line = line[:start_pos + 4] + new_attrs + line[start_pos + 3:]
                    lines[img_tag.sourceline - 1] = new_line
                    modified = True
            if modified:
                html_file.write_text('\n'.join(lines))
        # reporter.report_generic("image utilities finished")
