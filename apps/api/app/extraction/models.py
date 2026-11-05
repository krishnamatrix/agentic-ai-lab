from pydantic import BaseModel


class InteractionExtraction(BaseModel):
    person_name: str
    company_name: str
    interest: str
    next_action: str
    next_action_time: str

class PersonExtraction(BaseModel):
    student_address: str
    role: str
    company_name: str
