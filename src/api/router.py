from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from pydantic import HttpUrl

from src.api.dependencies import get_url_service
from src.models.schemas import ShortUrlDTO
from src.services.url_service import URLService

router = APIRouter()

@router.get("/{url_id}")
async def redirect(url_id: str,
                   url_service: URLService = Depends(get_url_service)) -> RedirectResponse:
    original_url = await url_service.get_original_url(url_id)
    if original_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                             detail="Not found")
    
    return RedirectResponse(original_url, 
                            status_code=status.HTTP_302_FOUND)

@router.post("/stats")
async def get_stats(status_token: UUID,
                    url_service: URLService = Depends(get_url_service)) -> ShortUrlDTO:
    short_url = await url_service.get_short_url_data(status_token)
    if short_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                             detail="Not found")
    
    return short_url


@router.post("/create")
async def create_short_url(url: HttpUrl,
                  url_service: URLService = Depends(get_url_service)) -> ShortUrlDTO:
    short_url = await url_service.create_short_url(url)

    return short_url
