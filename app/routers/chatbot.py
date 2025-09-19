from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any

from app.services import chatbot as service

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

MessageType = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    type: MessageType
    message: str
    timestamp: Any  # Firestore timestamp / datetime


class ChatSession(BaseModel):
    id: str
    history: List[ChatMessage]


class NewChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class AppendChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("/new", response_model=ChatSession, status_code=201)
async def new_chat(payload: NewChatRequest):
    data = service.create_session(payload.message)
    return data


@router.post("/{session_id}", response_model=ChatSession)
async def chat_continue(session_id: str, payload: AppendChatRequest):
    try:
        data = service.append_message(session_id, payload.message)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    return data
