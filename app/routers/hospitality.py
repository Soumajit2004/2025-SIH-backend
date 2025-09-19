from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
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
    location: Optional[dict] = None  # {lat, lng}
    images: Optional[List[dict]] = None  # list of {url, path, original, contentType}


class HospitalityCreate(BaseModel):
    type: HospitalityType
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    latitude: float
    longitude: float


class HospitalityUpdate(BaseModel):
    type: Optional[HospitalityType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def dict(self, *args, **kwargs):  # keep only provided keys
        data = super().dict(*args, **kwargs)
        return {k: v for k, v in data.items() if v is not None}


class HospitalityOut(HospitalityBase):
    id: str


@router.post("/", response_model=HospitalityOut, status_code=201, dependencies=[Depends(admin_required)])
async def create_hospitality(
    type: HospitalityType = Form(...),
    name: str = Form(..., min_length=1, max_length=200),
    description: str = Form(..., min_length=1, max_length=2000),
    latitude: float = Form(...),
    longitude: float = Form(...),
    images: List[UploadFile] = File(default_factory=list),
):
    # Read files into memory (could optimize with streaming if large)
    image_payload = []
    for f in images:
        try:
            content = await f.read()
        finally:
            await f.close()
        image_payload.append((f.filename, content, f.content_type))
    data = service.create_hospitality(
        htype=type.value,
        name=name,
        description=description,
        latitude=latitude,
        longitude=longitude,
        images=image_payload,
    )
    return data


@router.get("/", response_model=List[HospitalityOut])
async def list_hospitality():
    return service.list_hospitality()


@router.get("/{hid}", response_model=HospitalityOut)
async def get_hospitality(hid: str):
    data = service.get_hospitality(hid)
    if not data:
        raise HTTPException(status_code=404, detail="Not found")
    return data


@router.patch("/{hid}", response_model=HospitalityOut, dependencies=[Depends(admin_required)])
async def update_hospitality(
    hid: str,
    type: Optional[HospitalityType] = Form(None),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    new_images: List[UploadFile] = File(default_factory=list),
    replace_images: bool = Form(False),
):
    image_payload = []
    for f in new_images:
        try:
            content = await f.read()
        finally:
            await f.close()
        image_payload.append((f.filename, content, f.content_type))
    data = service.update_hospitality(
        hid,
        name=name,
        description=description,
        htype=type.value if type else None,
        latitude=latitude,
        longitude=longitude,
        new_images=image_payload if image_payload else None,
        replace_images=replace_images,
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
