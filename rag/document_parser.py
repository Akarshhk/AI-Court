import io
import os
import pypdf
import docx

def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extracts text from a given file byte stream based on the extension.
    Supported extensions: .txt, .pdf, .docx
    Raises ValueError for unsupported types or parsing failures, suitable for user-facing display.
    """
    ext = os.path.splitext(filename)[1].lower()
    text = ""
    
    if ext == ".txt":
        try:
            text = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode('latin-1')
            except Exception as e:
                raise ValueError("Could not read the .txt file. It appears to be corrupted or in an unsupported encoding.")
                
    elif ext == ".pdf":
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_file)
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
        except Exception as e:
            raise ValueError("Could not read the .pdf file. It might be corrupted, password-protected, or not a standard PDF.")
            
    elif ext == ".docx":
        try:
            docx_file = io.BytesIO(file_bytes)
            document = docx.Document(docx_file)
            paragraphs = []
            for para in document.paragraphs:
                paragraphs.append(para.text)
            text = "\n".join(paragraphs)
        except Exception as e:
            raise ValueError("Could not read the .docx file. It might be corrupted or not a valid Word document.")
            
    else:
        raise ValueError("Could not read this file — please upload a .txt, .pdf, or .docx file under 5MB.")
        
    text = text.strip()
    if len(text) < 50:
        raise ValueError("This document doesn't appear to contain readable text or is too short.")
        
    return text
