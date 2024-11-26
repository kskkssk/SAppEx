from app.api import app
from app.database import get_db
from app.service.crud.query_service import QueryService
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session


def get_guery_service(db: Session = Depends(get_db)):
    return QueryService(db)


@app.delete('/query')
def delete_query(query: str):
    try:
        query_service = get_guery_service()
        query_service.delete(query)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "Query deleted successfully"}
