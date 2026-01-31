'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import Cookies from 'js-cookie';
import { DocFile } from '@/types'; 

export default function Dashboard() {
  const router = useRouter();
  const [files, setFiles] = useState<DocFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const fetchFiles = async () => {
    try {
      const response = await api.get('/upload/files');
      setFiles(response.data);
    } catch (err) {
      console.error("Failed to fetch files", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Security Check
    const token = Cookies.get('token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchFiles();

    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchFiles, 5000);
    return () => clearInterval(interval); // Cleanup on exit
  }, [router]);

  // Handle file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', e.target.files[0]);

    try {
      await api.post('/upload/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      // Refresh
      fetchFiles();
    } catch (err) {
      alert("Upload failed! check console.");
      console.error(err);
    } finally {
      setUploading(false);
      e.target.value = ''; // Reset input so you can upload the same file again
    }
  };

  // --- 4. Logout Function ---
  const handleLogout = () => {
    Cookies.remove('token');
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      {/* Header */}
      <div className="max-w-5xl mx-auto flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          Docu<span className="text-blue-500">Flow</span> Dashboard
        </h1>
        <div className="flex gap-4 items-center">
            <button 
                onClick={handleLogout} 
                className="text-sm text-gray-400 hover:text-white transition px-3 py-2 rounded hover:bg-gray-800"
            >
                Sign Out
            </button>
            <label className={`cursor-pointer px-5 py-2.5 bg-blue-600 rounded-lg hover:bg-blue-700 transition font-medium shadow-lg shadow-blue-500/20 flex items-center gap-2 ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <span>{uploading ? 'Uploading...' : 'Upload PDF'}</span>
                <input type="file" accept=".pdf" className="hidden" onChange={handleFileUpload} disabled={uploading} />
            </label>
        </div>
      </div>

      {/* File List Table */}
      <div className="max-w-5xl mx-auto bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-2xl">
        {loading ? (
          <div className="p-12 text-center text-gray-400 animate-pulse">Loading secure documents...</div>
        ) : files.length === 0 ? (
          <div className="p-16 text-center">
             <div className="text-gray-500 text-lg mb-2">No documents found</div>
             <p className="text-gray-600 text-sm">Upload a PDF to start the analysis pipeline.</p>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-900/50 text-gray-400 uppercase text-xs tracking-wider font-semibold border-b border-gray-700">
              <tr>
                <th className="p-5">Document Name</th>
                <th className="p-5">Upload Date</th>
                <th className="p-5">Processing Status</th>
                <th className="p-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {files.map((file) => (
                <tr key={file._id} className="hover:bg-gray-700/50 transition duration-150 group">
                  <td className="p-5 font-medium text-gray-200 group-hover:text-white transition">{file.filename}</td>
                  <td className="p-5 text-gray-400 text-sm">
                    {new Date(file.upload_timestamp).toLocaleDateString()}
                  </td>
                  <td className="p-5">
                    {/* Status Badges */}
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border
                      ${file.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 
                        file.status === 'FAILED' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                        'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>
                      
                      {/* Pulsing Dot for Active States */}
                      {(file.status === 'PROCESSING' || file.status === 'PENDING') && (
                          <span className="w-1.5 h-1.5 mr-2 bg-yellow-400 rounded-full animate-pulse"></span>
                      )}
                      {file.status}
                    </span>
                  </td>
                  <td className="p-5 text-right">
                    {file.status === 'COMPLETED' && (
                        <button 
                            onClick={() => alert(file.extracted_text || "No text found.")}
                            className="text-blue-400 hover:text-blue-300 text-sm font-medium hover:underline focus:outline-none"
                        >
                            View Result
                        </button>
                    )}
                    {file.status === 'FAILED' && (
                        <span className="text-red-400 text-xs cursor-help" title={file.error}>Error details</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}