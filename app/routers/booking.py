from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Any, Dict

from app.utils.auth import get_current_user
from app.services import booking as booking_service


router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingCreate(BaseModel):
	hospitalityID: str = Field(..., min_length=1)
	startDate: datetime
	endDate: datetime
	ticketCount: int = Field(1, ge=1, le=100)

	@validator("endDate")
	def end_after_start(cls, v, values):  # type: ignore[override]
		start = values.get("startDate")
		if start and v <= start:
			raise ValueError("endDate must be after startDate")
		return v


class BookingOut(BaseModel):
	id: str
	hospitalityID: str
	startDate: datetime
	endDate: datetime
	user: str
	ticketCount: int
	createdOn: Optional[datetime] = None


@router.post("/", response_model=BookingOut, status_code=201)
async def create_booking(payload: BookingCreate, user=Depends(get_current_user)):
	data = booking_service.create_booking(
		user_id=user["id"],
		hospitality_id=payload.hospitalityID,
		start=payload.startDate,
		end=payload.endDate,
		ticket_count=payload.ticketCount,
	)
	return data


@router.get("/", response_model=List[BookingOut])
async def list_bookings(user=Depends(get_current_user)):
	return booking_service.list_bookings(user["id"])


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: str, user=Depends(get_current_user)):
	bk = booking_service.get_booking(user["id"], booking_id)
	if not bk:
		raise HTTPException(status_code=404, detail="Booking not found")
	return bk


@router.delete("/{booking_id}", status_code=204)
async def delete_booking(booking_id: str, user=Depends(get_current_user)):
	ok = booking_service.delete_booking(user["id"], booking_id)
	if not ok:
		raise HTTPException(status_code=404, detail="Booking not found")
	return None

