from fastapi import APIRouter, HTTPException, Depends, Response, BackgroundTasks, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import select
from authx import AuthX, AuthXConfig
from sqlalchemy import select

from .dependencies import SessionDep
from ..database import engine, Base
from ..schemas.books import BookSchema
from ..models.books import BookModel
from ..schemas.users import UserLoginSchema

import time
import asyncio

router = APIRouter()

config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY" #НИКОМУ НЕ ПОКАЗЫВАТЬ
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"] #ЗАНИМАЕТ ОЧЕНЬ МНОГО МЕСТА

security = AuthX(config=config)

#Database
@router.post("/setup_database", summary="Установка базы данных", tags=["База данных"])
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"Success": True, "Message": "База данных создалась"}


#Decorators?
@router.get("/", summary="Главная страница", tags=["Раздел 1"])
def Home():
    return "Hello world!"

@router.get("/books", summary="Получить все книги", tags=["Раздел 2"])
async def read_books(session: SessionDep):
    query = select(BookModel)
    result = await session.execute(query)

    return result.scalars().all()

@router.get("/books/{book_id}", summary="Получить определенную книгу", tags=["Раздел 2"])
async def get_book(book_id: int, session: SessionDep):
    query = select(BookModel).where(BookModel.id == book_id)
    result = await session.execute(query)
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Такой книги нет")
    
    return book

@router.post("/books", summary="Добавить книгу", tags=["Раздел 2"])
async def add_book(book: BookSchema, session: SessionDep):
    new_book = BookModel(
        title = book.title,
        author = book.author,
        year = book.year
    )
    session.add(new_book) #sql инъекции буэ
    await session.commit()

    return {"success": True, "Message": "Successfully added book"}


#Login
@router.post("/login", summary="Вход на сайт", tags=["Раздел 3"])
async def login(creds: UserLoginSchema, response: Response): #ДОРАБОТКА
    if(creds.username == "test" and creds.password == "test"):
        token = security.create_access_token(uid="12345")
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)

        return {"access_token": token}
    raise HTTPException(status_code=401, detail="Incorrect login or password")

@router.get("/protected", summary="Проверка прав пользователя", tags=["Раздел 3"], dependencies=[Depends(security.access_token_required)])
async def protected():
    return {"data": "TOP SECRET KEY"}


#Асинхронные и синхронные
#Если задача связана с сетью/БД → async + asyncio.
#Если это тяжёлые вычисления → sync + Celery.
#Если задача короткая → BackgroundTasks.
#Если задача долгая и критичная → Celery/RQ/ARQ (для асинхронных задач).
def sync_task():
    time.sleep(3)  # Блокирует выполнение на 3 секунды
    print("sync_task")

async def async_task():
    await asyncio.sleep(3) # Не блокирует, а "приостанавливает" выполнение
    print("async_task")

@router.post("/route", summary="Какая-то задача", tags=["Раздел 4"])
async def some_route(bg_tasks: BackgroundTasks):
    ...
    #asyncio.create_task(async_task()) # Не блокирует сервер
    bg_tasks.add_task(sync_task) # Запускается в отдельном потоке

    return {"Success": True, "Message": "Задача успешно выполнена"}


#Files
@router.post("/files", summary="Загрузка файла", tags=["Раздел 5"])
async def upload_file(uploaded_file: UploadFile):
    file = uploaded_file.file
    filename = uploaded_file.filename
    with open(f"{filename}_1", "wb") as f:
        f.write(file.read())

    return {"Success": True, "Message": "File uploaded successfully"}

@router.post("/multi_files", summary="Загрузка файлов", tags=["Раздел 5"])
async def upload_file(uploaded_files: list[UploadFile]):
    for uploaded_file in uploaded_files:
        file = uploaded_file.file
        filename = uploaded_file.filename
        with open(f"{filename}_1", "wb") as f: 
            f.write(file.read())

    return {"Success": True, "Message": "File uploaded successfully"}

@router.get("/files/{filename}", summary="Получить локальный файл", tags=["Раздел 5"])
async def get_file(filename: str):
    # if FileResponse(filename) == None:
    #     HTTPException(status_code=404,detail="Такого файла не существует")
    return FileResponse(filename)

def iterfile(filename: str):
    with open(filename, "rb") as file:
        while chunk := file.read(1024*1024):
            yield chunk


@router.get("/files/streaming/{filename}", summary="Получить видеофайл", tags=["Раздел 5"])
async def get_streaming_file(filename: str):
    return StreamingResponse(iterfile(filename), media_type="video/mp4") # вместо mp4 надо другое

  