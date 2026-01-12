# File Attachment Feature

This branch adds comprehensive file attachment support to the Terraform AI Assistant.

## New Features

### 1. File Upload API (`/v1/files/upload`)
- Upload files and automatically store them in RAG
- Supports multiple file formats:
  - **Documents**: PDF, DOCX, DOC
  - **Text files**: TXT, MD
  - **Code files**: PY, JS, TS, JAVA, CPP, C, GO, RS, TF
  - **Data files**: JSON, XML, YAML, CSV, HTML
  - **Scripts**: SH
- Automatic text extraction from uploaded files
- Optional metadata attachment
- File size validation (10MB limit)

### 2. File Management
- **GET /v1/files** - List uploaded files
- **GET /v1/files/{file_id}** - Get file content and metadata
- **DELETE /v1/files/{file_id}** - Delete uploaded file

### 3. Chat with Attachments
- Enhanced chat completions endpoint to accept file attachments
- Files can be attached to messages as base64-encoded content
- Automatic text extraction and inclusion in chat context
- Works with both streaming and non-streaming modes

## Technical Implementation

### New Files
- `app/utils/file_processor.py` - File processing utilities
- `app/api/v1/endpoints/files.py` - File upload endpoints

### Modified Files
- `app/schemas/requests.py` - Added FileAttachment, FileUploadResponse, FileListResponse models
- `app/api/v1/endpoints/chat.py` - Added attachment processing
- `app/api/v1/router.py` - Registered files router
- `requirements.txt` - Added PyPDF2 and python-docx

### Dependencies
- PyPDF2>=3.0.0 (PDF text extraction)
- python-docx>=1.0.0 (DOCX text extraction)

## Usage Examples

### Upload a file to RAG
```bash
curl -X POST "http://localhost:8000/v1/files/upload" \
  -F "file=@document.pdf" \
  -F "store_in_rag=true"
```

### Chat with file attachment
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze this code",
      "attachments": [
        {
          "filename": "main.py",
          "content": "base64_encoded_content",
          "mime_type": "text/x-python"
        }
      ]
    }
  ]
}
```

### List uploaded files
```bash
curl "http://localhost:8000/v1/files?limit=10"
```

## Installation

```bash
# Install new dependencies
pip install -r requirements.txt

# Or individually
pip install PyPDF2 python-docx
```

## Testing

The feature supports both:
1. **Direct file upload** - Files stored in RAG for future retrieval
2. **Inline attachments** - Files attached to chat messages for immediate context

Both approaches can be used together for maximum flexibility.
