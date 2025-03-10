from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from pdf_processor import pdf_manager
from llm_service import get_llm, get_response
from logger import setup_logger

logger = setup_logger()
app = FastAPI()

class ChatRequest(BaseModel):
    query: str
    api_key: str
    model_type: str
    model_name: str
    temperature: float
    max_tokens: int
    session_id: str

class PDFListResponse(BaseModel):
    pdfs: Dict[str, str]

@app.post("/upload")
async def upload_file(file: UploadFile):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        content = await file.read()
        pdf_id = pdf_manager.process_pdf(content, file.filename)
        
        return {"message": "PDF processed successfully", "pdf_id": pdf_id, "pdf_name": file.filename}
        
    except Exception as e:
        logger.error(f"Error in upload endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pdfs", response_model=PDFListResponse)
async def list_pdfs():
    try:
        pdfs = pdf_manager.list_pdfs()
        return {"pdfs": pdfs}
        
    except Exception as e:
        logger.error(f"Error listing PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/pdfs/{pdf_id}")
async def delete_pdf(pdf_id: str):
    try:
        if pdf_manager.remove_pdf(pdf_id):
            return {"message": f"PDF with ID {pdf_id} removed successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"PDF with ID {pdf_id} not found")
        
    except Exception as e:
        logger.error(f"Error removing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        llm = get_llm(
            request.model_type,
            request.model_name,
            request.api_key,
            request.temperature,
            request.max_tokens
        )
        
        response = get_response(llm, request.query)
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)