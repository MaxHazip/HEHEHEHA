from fastapi import FastAPI

app = FastAPI(title="Диспетчер")

@app.get(path="/")
async def test_endpoint():

    return {"message": "OK"}