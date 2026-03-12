"""Document parser for extracting text from various file formats"""

from pathlib import Path
from typing import Optional
import io


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file
    
    Args:
        file_content: PDF file content as bytes
        
    Returns:
        Extracted text as string
    """
    try:
        import pypdf
        
        pdf_file = io.BytesIO(file_content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except ImportError:
        raise ImportError("pypdf is required for PDF parsing. Install it with: pip install pypdf")
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    """
    Extract text from DOCX file
    
    Args:
        file_content: DOCX file content as bytes
        
    Returns:
        Extracted text as string
    """
    try:
        from docx import Document
        
        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except ImportError:
        raise ImportError("python-docx is required for DOCX parsing. Install it with: pip install python-docx")
    except Exception as e:
        raise Exception(f"Error parsing DOCX: {str(e)}")


def extract_text_from_doc(file_content: bytes) -> str:
    """
    Extract text from DOC file (older Word format)
    
    Args:
        file_content: DOC file content as bytes
        
    Returns:
        Extracted text as string
    """
    try:
        import textract
        
        # Save to temporary file as textract needs a file path
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.doc') as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        text = textract.process(tmp_path).decode('utf-8')
        
        # Clean up temp file
        Path(tmp_path).unlink()
        
        return text.strip()
    except ImportError:
        raise ImportError("textract is required for DOC parsing. Install it with: pip install textract")
    except Exception as e:
        raise Exception(f"Error parsing DOC: {str(e)}")


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text from various file formats
    
    Args:
        file_content: File content as bytes
        filename: Original filename to determine file type
        
    Returns:
        Extracted text as string
    """
    file_extension = Path(filename).suffix.lower()
    
    if file_extension == '.txt':
        return file_content.decode('utf-8', errors='ignore')
    elif file_extension == '.pdf':
        return extract_text_from_pdf(file_content)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_content)
    elif file_extension == '.doc':
        return extract_text_from_doc(file_content)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


def is_supported_format(filename: str) -> bool:
    """
    Check if file format is supported
    
    Args:
        filename: Filename to check
        
    Returns:
        True if supported, False otherwise
    """
    supported_extensions = ['.txt', '.pdf', '.docx', '.doc']
    file_extension = Path(filename).suffix.lower()
    return file_extension in supported_extensions
