#Libraries
from fastapi import FastAPI, HTTPException, Depends, Response, BackgroundTasks, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select
from authx import AuthX, AuthXConfig
from typing import Annotated
from datetime import datetime
import time
import asyncio
import uvicorn


#Classes
class BookSchema(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=30)
    year: int = Field(ge=500, le=datetime.now().year)

    model_config = ConfigDict(extra='forbid')

class Base(DeclarativeBase):
    pass

class BookModel(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author: Mapped[str]
    year: Mapped[int]

class UserLoginSchema(BaseModel):
    username: str
    password: str


#Start
app = FastAPI()
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True) #if Docker [host="0.0.0.0"]

engine = create_async_engine('sqlite+aiosqlite:///books.db')
new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY" #НИКОМУ НЕ ПОКАЗЫВАТЬ
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"] #ЗАНИМАЕТ ОЧЕНЬ МНОГО МЕСТА

security = AuthX(config=config)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


#Database
@app.post("/setup_database", summary="Установка базы данных", tags=["База данных"])
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"Success": True, "Message": "База данных создалась"}


#Demo data
books = [
    {
        "id": 1,
        "title": "Tokyo Ghoul",
        "author": "Sui Ishida",
        "year": "2014"
    },
    {
        "id": 2,
        "title": "Kaguya-sama: Love Is War",
        "author": "Aka Akasaka",
        "year": "2015"
    },
]


#Decorators?
@app.get("/", summary="Главная страница", tags=["Раздел 1"])
def Home():
    return "Hello world!"

@app.get("/books", summary="Получить все книги", tags=["Раздел 2"])
async def read_books(session: SessionDep):
    query = select(BookModel)
    result = await session.execute(query)

    return result.scalars().all()

@app.get("/books/{book_id}", summary="Получить определенную книгу", tags=["Раздел 2"])
async def get_book(book_id: int, session: SessionDep):
    query = select(BookModel).where(BookModel.id == book_id)
    result = await session.execute(query)
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Такой книги нет")
    
    return book

@app.post("/books", summary="Добавить книгу", tags=["Раздел 2"])
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
@app.post("/login", summary="Вход на сайт", tags=["Раздел 3"])
async def login(creds: UserLoginSchema, response: Response): #ДОРАБОТКА
    if(creds.username == "test" and creds.password == "test"):
        token = security.create_access_token(uid="12345")
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)

        return {"access_token": token}
    raise HTTPException(status_code=401, detail="Incorrect login or password")

@app.get("/protected", summary="Проверка прав пользователя", tags=["Раздел 3"], dependencies=[Depends(security.access_token_required)])
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

@app.post("/route", summary="Какая-то задача", tags=["Раздел 4"])
async def some_route(bg_tasks: BackgroundTasks):
    ...
    #asyncio.create_task(async_task()) # Не блокирует сервер
    bg_tasks.add_task(sync_task) # Запускается в отдельном потоке

    return {"Success": True, "Message": "Задача успешно выполнена"}


#Files
@app.post("/files", summary="Загрузка файла", tags=["Раздел 5"])
async def upload_file(uploaded_file: UploadFile):
    file = uploaded_file.file
    filename = uploaded_file.filename
    with open(f"{filename}_1", "wb") as f:
        f.write(file.read())

    return {"Success": True, "Message": "File uploaded successfully"}

@app.post("/multi_files", summary="Загрузка файлов", tags=["Раздел 5"])
async def upload_file(uploaded_files: list[UploadFile]):
    for uploaded_file in uploaded_files:
        file = uploaded_file.file
        filename = uploaded_file.filename
        with open(f"{filename}_1", "wb") as f: 
            f.write(file.read())

    return {"Success": True, "Message": "File uploaded successfully"}

@app.get("/files/{filename}", summary="Получить локальный файл", tags=["Раздел 5"])
async def get_file(filename: str):
    return FileResponse(filename)

def iterfile(filename: str):
    with open(filename, "rb") as file:
        while chunk := file.read(1024*1024):
            yield chunk


@app.get("/files/streaming/{filename}", summary="Получить облачный файл ", tags=["Раздел 5"])
async def get_streaming_file(filename: str):
    return StreamingResponse(iterfile(filename), media_type="video/mp4") # вместо mp4 надо другое

  