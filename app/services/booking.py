"""Booking service layer wrapping Firestore operations."""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime

from app.utils.firebase import get_firestore, server_timestamp

BOOKINGS_COLLECTION = "bookings"


def _collection(user_id: str):
	db = get_firestore()
	return db.collection(BOOKINGS_COLLECTION)


def create_booking(*, user_id: str, hospitality_id: str, start: datetime, end: datetime, ticket_count: int = 1) -> Dict[str, Any]:
	db = get_firestore()
	doc_ref = db.collection(BOOKINGS_COLLECTION).document()
	payload = {
		"hospitalityID": hospitality_id,
		"startDate": start,
		"endDate": end,
		"user": user_id,  # storing just uid; could store a DocumentReference if desired
		"ticketCount": ticket_count,
		"createdOn": server_timestamp(),
	}
	doc_ref.set(payload)
	payload["id"] = doc_ref.id
	return payload


def list_bookings(user_id: str) -> List[Dict[str, Any]]:
	db = get_firestore()
	q = db.collection(BOOKINGS_COLLECTION).where("user", "==", user_id).order_by("createdOn", direction="DESCENDING")
	docs = q.stream()
	out: List[Dict[str, Any]] = []
	for d in docs:
		data = d.to_dict() or {}
		data["id"] = d.id
		out.append(data)
	return out


def get_booking(user_id: str, booking_id: str) -> Optional[Dict[str, Any]]:
	db = get_firestore()
	ref = db.collection(BOOKINGS_COLLECTION).document(booking_id)
	snap = ref.get()
	if not snap.exists:
		return None
	data = snap.to_dict() or {}
	if data.get("user") != user_id:
		return None
	data["id"] = snap.id
	return data


def delete_booking(user_id: str, booking_id: str) -> bool:
	db = get_firestore()
	ref = db.collection(BOOKINGS_COLLECTION).document(booking_id)
	snap = ref.get()
	if not snap.exists:
		return False
	data = snap.to_dict() or {}
	if data.get("user") != user_id:
		return False
	ref.delete()
	return True

