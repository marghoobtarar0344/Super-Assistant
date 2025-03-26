from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.config import Config
from routing.virtual_assistant_routing import router as chat_router

app = FastAPI(title=Config.APP_NAME)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'd want to specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat_router, prefix="")
"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)"""