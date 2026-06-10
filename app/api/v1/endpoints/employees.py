from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.department import Department
from app.models.employee import Employee

router = APIRouter()


class EmployeeProfileResponse(BaseModel):
    employee_id: int
    employee_name: str
    position: str
    department_id: int
    department_name: str
    monthly_budget_limit: float


@router.get("/{employee_id}", response_model=EmployeeProfileResponse)
async def get_employee_profile(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            Employee,
            Department.department_name,
            Department.monthly_budget_limit,
        )
        .join(Department, Employee.department_id == Department.department_id)
        .where(Employee.employee_id == employee_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    emp, dept_name, budget_limit = row
    return EmployeeProfileResponse(
        employee_id=emp.employee_id,
        employee_name=emp.employee_name,
        position=emp.position,
        department_id=emp.department_id,
        department_name=dept_name,
        monthly_budget_limit=float(budget_limit or 0),
    )
