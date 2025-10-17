# services/test_generation/app.py
from fastapi import FastAPI
from .main import router as test_gen_router  # <-- use relative import

app = FastAPI(title="Test Generation Service", version="1.0")

# Mount the router at root
app.include_router(test_gen_router, prefix="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "services.test_generation.app:app",  # module:app
        host="127.0.0.1",
        port=8002,
        reload=True
    )
