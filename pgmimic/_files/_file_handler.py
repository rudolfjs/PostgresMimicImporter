import glob


class FileHandler:
    def __init__(self) -> None:
        return None

    def path(self, path: str = None) -> None:
        """
        Set the file path for data
        Args:
            path (str): System path for file location
        """
        self.path = path
        if self._exists(self.path) is False:
            raise FileNotFoundError
        return None

    def _exists(self, path) -> bool:
        """
        Check if the data is stored in the provided path
        """
        files = glob.glob(path + "/**/*.csv.gz", recursive=True)
        if len(files) > 0:
            return True
        else:
            return False

    def files(self) -> list:
        files = glob.glob(self.path + "/**/*.csv.gz", recursive=True)
        return files
