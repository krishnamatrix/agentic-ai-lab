from pydantic import BaseModel, Field


class Company(BaseModel):
    id: str
    name: str
    industry: str | None = None
    employee_count: int | None = None
    annual_revenue: float | None = None
    headquarters: str | None = None
    website: str | None = None

