from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    NURSE = "nurse"
    DOCTOR = "doctor"


ALL_ROLES = tuple(r.value for r in Role)
CLINICAL_ROLES = (Role.NURSE.value, Role.DOCTOR.value)
