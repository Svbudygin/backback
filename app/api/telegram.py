from aiogram import Bot, types
from aiogram.types import BufferedInputFile, InlineKeyboardButton, BufferedInputFile, InputMediaDocument
from fastapi import UploadFile
from aiogram.exceptions import AiogramError, TelegramAPIError
from PyPDF2 import PdfMerger
from PIL import Image
from io import BytesIO

from app.exceptions import TelegramException


async def merge_files_to_pdf(buffers: list[tuple[str, BytesIO]]) -> BytesIO:
    merger = PdfMerger()

    for filename, buffer in buffers:
        buffer.seek(0)
        if filename.lower().endswith(".pdf"):
            merger.append(buffer)
        elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
            img = Image.open(buffer).convert("RGB")
            img_pdf = BytesIO()
            img.save(img_pdf, format="PDF")
            img_pdf.seek(0)
            merger.append(img_pdf)
        else:
            print(f"Unsupported file type: {filename}")

    output = BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return output


async def send_to_chat(api_secret: str, chat_id: str, message: str, message_for_multi: str,
                       decline_callback: str, accept_callback: str,
                       files: list[tuple[str, BytesIO]]):
    bot = Bot(token=api_secret)
    markup = types.InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='✅', callback_data=accept_callback),
        InlineKeyboardButton(text='Удалить', callback_data=decline_callback)
    ]])
    try:
        if len(files) == 1:
            filename, buffer = files[0]
            buffer.seek(0)
            await bot.send_document(
                document=BufferedInputFile(file=buffer.read(), filename=filename),
                chat_id=chat_id,
                caption=message,
                reply_markup=markup,
                parse_mode='markdown'
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=markup,
                parse_mode='markdown'
            )
            media = []
            for i, (filename, buffer) in enumerate(files):
                is_last = i == len(files) - 1
                buffer.seek(0)
                media.append(InputMediaDocument(
                    media=BufferedInputFile(buffer.read(), filename=filename),
                    caption=message_for_multi if is_last else None,
                    parse_mode='markdown' if is_last else None
                ))
            await bot.send_media_group(chat_id=chat_id, media=media)
        await bot.session.close()
    except AiogramError as err:
        raise TelegramException(detail=str(err))


async def send_appeal(api_secret: str, chat_id: str, message: str,
                      files: list[UploadFile] | None):
    bot = Bot(token=api_secret)
    
    try:
        if files is not None:
            file = files[0]
            await bot.send_document(document=BufferedInputFile(file=file.file.read(), filename=file.filename),
                                    chat_id=chat_id,
                                    caption=message,
                                    parse_mode='markdown'
                                    )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='markdown'
            )
        await bot.session.close()
    except AiogramError as err:
        raise TelegramException(detail=str(err))
