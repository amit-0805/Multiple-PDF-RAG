from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import tempfile
import os
import uuid
from logger import setup_logger

logger = setup_logger()

class PDFManager:
    def __init__(self):
        self.vectorstores = {}
        self.pdf_names = {}
        self.documents = {}  # Add a dictionary to store documents by PDF ID
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.combined_vectorstore = None
    
    def process_pdf(self, file_content: bytes, file_name: str) -> str:
        try:
            # Generate a unique ID for this PDF
            pdf_id = str(uuid.uuid4())
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
                
            logger.info(f"Processing PDF file: {file_name}")
            
            # Load and process the PDF
            loader = PyPDFLoader(tmp_path)
            pages = loader.load()
            
            # Add metadata to each document to track which PDF it came from
            for page in pages:
                page.metadata["source"] = file_name
                page.metadata["pdf_id"] = pdf_id
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            splits = text_splitter.split_documents(pages)
            
            # Store the original document chunks
            self.documents[pdf_id] = splits
            
            # Create vector store for this specific PDF
            vectorstore = FAISS.from_documents(splits, self.embeddings)
            
            # Store the vectorstore and PDF name
            self.vectorstores[pdf_id] = vectorstore
            self.pdf_names[pdf_id] = file_name
            
            # Update the combined vectorstore
            self._update_combined_vectorstore()
            
            logger.info(f"PDF {file_name} processed successfully with ID: {pdf_id}")
            
            return pdf_id
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
            
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.info("Temporary PDF file cleaned up")
    
    def _update_combined_vectorstore(self):
        """Update the combined vectorstore with all documents from all PDFs"""
        if not self.vectorstores:
            return
        
        if len(self.vectorstores) == 1:
            # If there's only one PDF, use its vectorstore as the combined one
            pdf_id = list(self.vectorstores.keys())[0]
            self.combined_vectorstore = self.vectorstores[pdf_id]
        else:
            # Combine all documents from all vectorstores
            all_docs = []
            for pdf_id in self.documents:
                # Get documents directly from the stored documents dictionary
                all_docs.extend(self.documents[pdf_id])
            
            # Create a new combined vectorstore
            self.combined_vectorstore = FAISS.from_documents(all_docs, self.embeddings)
    
    def get_combined_vectorstore(self):
        """Get the combined vectorstore for querying across all PDFs"""
        return self.combined_vectorstore
    
    def get_pdf_name(self, pdf_id):
        """Get the PDF name for a given PDF ID"""
        return self.pdf_names.get(pdf_id)
    
    def list_pdfs(self):
        """Return a list of all PDFs with their IDs and names"""
        return {pdf_id: name for pdf_id, name in self.pdf_names.items()}
    
    def remove_pdf(self, pdf_id):
        """Remove a PDF from the manager"""
        if pdf_id in self.vectorstores:
            del self.vectorstores[pdf_id]
            del self.pdf_names[pdf_id]
            if pdf_id in self.documents:
                del self.documents[pdf_id]
            self._update_combined_vectorstore()
            return True
        return False

# Create a global instance of the PDF manager
pdf_manager = PDFManager()