from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import Dict, List, Any, AsyncGenerator
import os

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you'd want to specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def healthcheck():
    """Health check endpoint."""
    return {
        "status": "OK",
        "message": "SuperCar Virtual Sales Assistant API is running! Replace this with your implementation."
    } 