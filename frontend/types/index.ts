// Auth Response from backend
export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// File object type(received from database)
export interface DocFile {
  _id: string;
  filename: string;
  // Status
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'; 
  upload_timestamp: string;
  extracted_text?: string;
  error?: string;
}