from fastapi.security import HTTPBearer
from fastapi import Depends

security = HTTPBearer()


def get_token(token=Depends(security)):
    return token
