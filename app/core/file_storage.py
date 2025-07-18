import uuid
from datetime import datetime
import aioboto3

from app.core.config import settings
from app.exceptions import FileNotFoundException

async_session = aioboto3.Session(
    aws_access_key_id=settings.FILE_STORAGE_KEY,
    aws_secret_access_key=settings.FILE_STORAGE_SECRET,
    region_name=settings.FILE_STORAGE_LOCATION,
)


async def upload_file(file, filename: str, bucket=settings.FILE_STORAGE_BUCKET) -> str:
    async with async_session.client("s3") as session:
        date = datetime.utcnow().strftime("%Y-%m-%d")
        folder = settings.FILE_STORAGE_PATH
        path = f"{folder}{date}-{str(uuid.uuid4())}-{filename}"
        file.seek(0)

        await session.put_object(
            Body=file.read(), Bucket=bucket, Key=path
        )
        return path


async def upload_files(files: list, bucket=settings.FILE_STORAGE_BUCKET) -> list[str]:
    async with async_session.client("s3") as session:
        paths = []
        folder = settings.FILE_STORAGE_PATH
        for file in files:
            date = datetime.utcnow().strftime("%Y-%m-%d")
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            path = f"{folder}{date}-{str(uuid.uuid4())}.{file_extension}"
            file.file.seek(0)

            await session.put_object(
                Body=file.file.read(),
                Bucket=bucket,
                Key=path
            )
            paths.append(path)
        return paths


async def download_file(path: str):
    async with async_session.client("s3") as session:
        folder = settings.FILE_STORAGE_PATH
        path = f"{folder}{path}"
        result = await session.get_object(
            Bucket=settings.FILE_STORAGE_BUCKET,
            Key=path,
        )
        async for chunk in result["Body"]:
            yield chunk


def get_s3_url(*, bucket_name: str, region: str, file_path: str) -> str:
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_path}"


async def get_file_by_key(key):
    async with async_session.client("s3") as s3:
        folder = settings.FILE_STORAGE_PATH
        path = f"{folder}{key}"
        try:
            result = await s3.get_object(
                Bucket=settings.FILE_STORAGE_BUCKET,
                Key=path
            )

            return await result["Body"].read()
        except Exception as e:
            print(e)
            raise FileNotFoundException()


async def get_presigned_url(file_key: str) -> str:
    folder = settings.FILE_STORAGE_PATH
    path = f"{folder}{file_key}"

    async with async_session.client("s3") as s3:
        url = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.FILE_STORAGE_BUCKET, "Key": path},
            ExpiresIn=600,
        )

        return url
