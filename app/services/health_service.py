from app.core.config import Settings
from app.core.database import Database
from app.models.common import SystemHealthData, DatabaseHealthDetails


class HealthService:
    """Service handling application & database status evaluation."""

    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    async def get_system_health(self) -> SystemHealthData:
        """
        Evaluates system health and database connectivity.
        Explicitly marks system status as 'degraded' if MongoDB ping fails.
        """
        db_health = await self.db.check_health()
        
        db_details = DatabaseHealthDetails(
            connected=db_health["connected"],
            database_name=db_health["database_name"],
            error=db_health["error"]
        )
        
        # Determine overall system health status
        status = "healthy" if db_details.connected else "degraded"
        
        return SystemHealthData(
            app_name=self.settings.APP_NAME,
            version=self.settings.APP_VERSION,
            environment=self.settings.APP_ENV,
            status=status,
            database=db_details
        )
