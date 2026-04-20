from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.plugin import hookimpl


class CombinedReadmeMetadataHook(MetadataHookInterface):
    PLUGIN_NAME = "combined-readme"

    def update(self, metadata):
        readme = Path("README.md").read_text(encoding="utf-8")
        history = Path("HISTORY.md").read_text(encoding="utf-8")

        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": readme + "\n\n---\n\n" + history,
        }


@hookimpl
def hatch_register_metadata_hook() -> type[MetadataHookInterface]:
    return CombinedReadmeMetadataHook
