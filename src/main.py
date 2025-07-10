#Libraries
from fastapi import FastAPI

from src.api import main_router

#Start
app = FastAPI()
app.include_router(main_router)

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run("src.main:app", reload=True) #if Docker [host="0.0.0.0"]


