import glob


class FileHandler:
    def __init__(self) -> None:
        self._path: str | None = None

    def path(self, path: str) -> str:
        """
        Set the file path for data and return it.

        Args:
            path: System path for file location.

        Returns:
            The validated path, so callers can chain or capture it.
        """
        self._path = path
        if self._exists(self._path) is False:
            raise FileNotFoundError(path)
        return self._path

    def _exists(self, path: str) -> bool:
        """
        Check if the data is stored in the provided path
        """
        files = glob.glob(path + "/**/*.csv.gz", recursive=True)
        return len(files) > 0

    def files(self) -> list[str]:
        if self._path is None:
            raise RuntimeError("FileHandler.path() must be called before files()")
        return glob.glob(self._path + "/**/*.csv.gz", recursive=True)
