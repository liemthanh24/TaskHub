from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Kiểm tra trạng thái dịch vụ")
async def health_check():
    return {"status": "ok"}
