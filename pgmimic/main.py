from importer.mimic_importer import MimicImporter


def main():
    mimic_importer = MimicImporter("config.json")
    # Config will have db and file location config
    mimic_importer.connect()
    mimic_importer.import_mimic()
    mimic_importer.close()
    return None


if __name__ == "__main__":
    main()
