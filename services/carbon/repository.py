"""Carbon project repository — database-backed persistence for carbon projects."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.models import CarbonProject


class CarbonProjectRepository:
    """Repository for carbon project CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_project(
        self,
        project_id: str,
        name: str,
        project_type: str = "afforestation",
        area_ha: float = 0.0,
        user_id: Optional[str] = None,
        status: str = "draft",
        credits_issued: float = 0.0,
        **kwargs,
    ) -> CarbonProject:
        """Create a new carbon project."""
        project = CarbonProject(
            project_id=project_id,
            name=name,
            user_id=user_id,
            project_type=project_type,
            area_hectares=area_ha,
            status=status,
            credits_issued=credits_issued,
            registered_at=datetime.utcnow() if status in ("registered", "verified", "certified") else None,
            **kwargs,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: str) -> Optional[CarbonProject]:
        """Get project by project_id."""
        return self.db.query(CarbonProject).filter(CarbonProject.project_id == project_id).first()

    def get_project_by_db_id(self, db_id: int) -> Optional[CarbonProject]:
        """Get project by database ID."""
        return self.db.query(CarbonProject).filter(CarbonProject.id == db_id).first()

    def list_projects(self, user_id: Optional[str] = None, status: Optional[str] = None):
        """List projects with optional filters."""
        query = self.db.query(CarbonProject)
        if user_id is not None:
            query = query.filter(CarbonProject.user_id == user_id)
        if status is not None:
            query = query.filter(CarbonProject.status == status)
        return query.order_by(CarbonProject.registered_at.desc()).all()

    def update_project(self, project_id: str, **kwargs) -> Optional[CarbonProject]:
        """Update project fields."""
        project = self.get_project(project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        project = self.get_project(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True
