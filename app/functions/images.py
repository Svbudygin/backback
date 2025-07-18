import io
from typing import List

from fastapi import UploadFile
from PIL import Image

from app.exceptions import InvalideFileTypeException

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # Max 10MB


# async def validate_image(file: UploadFile):
#     """
#     Проверяет, что загруженный файл представляет собой изображение
#     и что его размер не больше MAX_FILE_SIZE_BYTES
#     """
#     if not file.content_type.startswith("image/"):
#         raise ValueError("File is not an image")
#
#     file.file.seek(0, io.SEEK_END)
#     file_size = file.file.tell()
#     file.file.seek(0)
#
#     if file_size > MAX_FILE_SIZE_BYTES:
#         raise ValueError("File size exceeds max file size")
#
#     return True


async def validate_file(file: UploadFile, allow_pdf: bool = False):
    """
    Проверяет, что загруженный файл представляет собой изображение или PDF (если allow_pdf=True)
    и что его размер не больше MAX_FILE_SIZE_BYTES
    """
    if allow_pdf:
        if not (
            file.content_type.startswith("image/")
            or file.content_type == "application/pdf"
        ):
            raise InvalideFileTypeException()
    else:
        if not file.content_type.startswith("image/"):
            raise InvalideFileTypeException()

    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError("File size exceeds max file size")


async def merge_images(images: List[Image.Image]) -> Image.Image:
    """
    Соединяет картинки горизонтально
    """
    widths, heights = zip(*(img.size for img in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_image = Image.new("RGB", (total_width, max_height))

    x_offset = 0
    for img in images:
        new_image.paste(img, (x_offset, 0))
        x_offset += img.width

    return new_image


async def read_image(file: UploadFile) -> Image.Image:
    contents = await file.read()
    return Image.open(io.BytesIO(contents))
