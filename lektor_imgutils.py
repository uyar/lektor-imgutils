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
            content = html_file.read_text()
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
                    img_tag.attrs.update(img_data)
                    html_file.write_text(str(soup))
        # reporter.report_generic("image utilities finished")
