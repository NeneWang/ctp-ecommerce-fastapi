from fastapi import  UploadFile, Path, HTTPException, status
def raiseExceptionIfRowIsNone(rows, SQL_QUERY=""):
    """
    Raises 404 Not found if query is not found
    Query is shown for debugging.
    """
    if(rows is None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query: {SQL_QUERY}",
        )
