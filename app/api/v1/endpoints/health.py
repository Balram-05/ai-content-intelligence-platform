from fastapi import APIRouter, Depends, status, Response
from app.models.common import StandardAPIResponse, SystemHealthData
from app.services.health_service import HealthService
from app.api.dependencies import get_health_service

router = APIRouter()


@router.get(
    "/health",
    response_model=StandardAPIResponse[SystemHealthData],
    summary="Get system health status",
    description="Evaluates system status and explicitly checks MongoDB connectivity."
)
async def check_health(
    response: Response,
    health_service: HealthService = Depends(get_health_service)
) -> StandardAPIResponse[SystemHealthData]:
    health_data = await health_service.get_system_health()
    
    if health_data.status != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return StandardAPIResponse(
            status="degraded",
            message="System operational but database connection is degraded or unavailable",
            data=health_data,
            error={"database_error": health_data.database.error}
        )
        
    return StandardAPIResponse(
        status="success",
        message="System and database are fully operational",
        data=health_data
    )
