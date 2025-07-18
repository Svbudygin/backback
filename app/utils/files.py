import os

from fastapi import UploadFile


def get_file_extension(file: UploadFile) -> str:
    """
    Возвращает расширение файла в формате .расширение
    """
    return os.path.splitext(file.filename)[1].lower()
