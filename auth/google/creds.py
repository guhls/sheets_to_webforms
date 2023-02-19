import os.path

from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

dirname = os.path.dirname(__file__)
filename_credentials = os.path.join(dirname, "credentials.json")


def get_creds():
    creds = Credentials.from_service_account_file(
        filename=filename_credentials, scopes=SCOPES
    )
    return creds


if __name__ == "__main__":
    get_creds()
