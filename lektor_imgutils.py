from pathlib import Path

from lektor.pluginsystem import Plugin
from lektor.reporter import reporter


class ImgUtilsPlugin(Plugin):
    name = "lektor-imgutils"
    description = "Image handling utilities."

    def on_after_build_all(self, builder, **extra):
        reporter.report_generic("image utilities started")
        for html_file in Path(builder.destination_path).glob("**/*.html"):
            reporter.report_generic(html_file)
        reporter.report_generic("image utilities finished")
