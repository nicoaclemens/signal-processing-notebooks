from __future__ import annotations

from tornado.web import HTTPError

try:
    from jupyter_server.services.contents.largefilemanager import LargeFileManager
except ImportError:  # pragma: no cover
    from notebook.services.contents.largefilemanager import LargeFileManager


class ReadOnlyContentsManager(LargeFileManager):
    """Jupyter contents manager that allows read-only access to workspace files."""

    def _deny(self, action: str, path: str = "") -> None:
        raise HTTPError(403, f"Read-only mode: {action} is disabled for '{path}'.")

    def save(self, model, path=""):
        self._deny("save", path)

    def delete_file(self, path):
        self._deny("delete", path)

    def rename_file(self, old_path, new_path):
        self._deny("rename", f"{old_path} -> {new_path}")

    def copy(self, from_path, to_path=None):
        self._deny("copy", f"{from_path} -> {to_path or ''}")

    def new_untitled(self, path="", type="", ext=""):
        self._deny("create", path)

    def create_checkpoint(self, path):
        self._deny("checkpoint create", path)

    def restore_checkpoint(self, checkpoint_id, path):
        self._deny("checkpoint restore", path)

    def delete_checkpoint(self, checkpoint_id, path):
        self._deny("checkpoint delete", path)

    def rename_checkpoint(self, checkpoint_id, old_path, new_path):
        self._deny("checkpoint rename", f"{old_path} -> {new_path}")
