'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import Link from 'next/link';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // 1. Frontend Validation
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
        setError("Password must be at least 6 characters");
        return;
    }
    
    try {
      await api.post('/auth/register', { email, password });
      
      setSuccess(true);
      
      // Auto-redirect after 2 seconds
      setTimeout(() => {
        router.push('/login');
      }, 2000);

    } catch (err: any) {
      if (err.response?.status === 400) {
        setError('This email is already registered.');
      } else {
        setError('Registration failed. Please try again.');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-96 border border-gray-700">
        <h2 className="text-2xl font-bold mb-6 text-center">Create Account</h2>
        
        {/* Error Banner */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-200 p-3 rounded mb-4 text-sm text-center">
            {error}
          </div>
        )}

        {/* Success Banner */}
        {success ? (
           <div className="bg-green-500/10 border border-green-500/50 text-green-200 p-4 rounded mb-4 text-center">
             <p className="font-bold">Account Created!</p>
             <p className="text-sm mt-1">Redirecting to login...</p>
           </div>
        ) : (
            <form onSubmit={handleRegister} className="space-y-4">
            <div>
                <label className="block text-gray-400 mb-1 text-sm">Email Address</label>
                <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="user@example.com"
                required 
                />
            </div>
            
            <div>
                <label className="block text-gray-400 mb-1 text-sm">Password</label>
                <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="••••••••"
                required 
                />
            </div>

            <div>
                <label className="block text-gray-400 mb-1 text-sm">Confirm Password</label>
                <input 
                type="password" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="••••••••"
                required 
                />
            </div>

            <button 
                type="submit" 
                className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded font-semibold transition shadow-lg mt-2"
            >
                Sign Up
            </button>
            </form>
        )}
        
        <div className="mt-6 text-center text-sm text-gray-400">
          Already have an account? <Link href="/login" className="text-blue-400 hover:underline">Login here</Link>
        </div>
      </div>
    </div>
  );
}