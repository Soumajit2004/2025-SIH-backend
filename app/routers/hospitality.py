from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

from app.utils.auth import get_current_user, admin_required
from app.services import hospitality as service

router = APIRouter(prefix="/hospitality", tags=["hospitality"])


class HospitalityType(str, Enum):
    attraction = "attraction"
    hotel = "hotel"
    restaurant = "restaurant"


class HospitalityBase(BaseModel):
    type: HospitalityType
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)


class HospitalityCreate(HospitalityBase):
    pass


class HospitalityUpdate(BaseModel):
    type: Optional[HospitalityType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)

    def dict(self, *args, **kwargs):  # keep only provided keys
        data = super().dict(*args, **kwargs)
        return {k: v for k, v in data.items() if v is not None}


class HospitalityOut(HospitalityBase):
    id: str


@router.post("/", response_model=HospitalityOut, status_code=201, dependencies=[Depends(admin_required)])
async def create_hospitality(payload: HospitalityCreate):
    data = service.create_hospitality(htype=payload.type.value, name=payload.name, description=payload.description)
    return data


@router.get("/", response_model=List[HospitalityOut])
async def list_hospitality(user=Depends(get_current_user)):
    return service.list_hospitality()


@router.get("/{hid}", response_model=HospitalityOut)
async def get_hospitality(hid: str, user=Depends(get_current_user)):
    data = service.get_hospitality(hid)
    if not data:
        raise HTTPException(status_code=404, detail="Not found")
    return data


@router.patch("/{hid}", response_model=HospitalityOut, dependencies=[Depends(admin_required)])
async def update_hospitality(hid: str, payload: HospitalityUpdate):
    updates = payload.dict()
    type_obj = updates.get("type")
    htype = type_obj.value if type_obj is not None else None
    data = service.update_hospitality(
        hid,
        name=updates.get("name"),
        description=updates.get("description"),
        htype=htype,
    )
    if not data:
        raise HTTPException(status_code=404, detail="Not found")
    return data


@router.delete("/{hid}", status_code=204, dependencies=[Depends(admin_required)])
async def delete_hospitality(hid: str):
    ok = service.delete_hospitality(hid)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return None
