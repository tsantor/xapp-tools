from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface


class CombinedReadmeMetadataHook(MetadataHookInterface):
    PLUGIN_NAME = "combined-readme"

    def update(self, metadata):
        readme = Path("README.md").read_text(encoding="utf-8")
        history = Path("HISTORY.md").read_text(encoding="utf-8")

        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": readme + "\n\n---\n\n" + history,
        }
