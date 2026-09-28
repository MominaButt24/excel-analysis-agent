import pandas as pd


def parse_xlsx(file_path: str) -> dict[str, pd.DataFrame]:
    """
    Parse an XLSX file and return each sheet as a DataFrame.
    """

    sheets = pd.read_excel(
        file_path,
        sheet_name=None
    )

    return sheets