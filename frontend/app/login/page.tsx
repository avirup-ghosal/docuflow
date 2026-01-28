'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import Cookies from 'js-cookie';
import Link from 'next/link';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await api.post('/auth/login', { email, password });
      
      //Save the Token securely in a Cookie
      Cookies.set('token', response.data.access_token);
      
      //Redirect to the Dashboard
      router.push('/dashboard');
    } catch (err: any) {
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-96 border border-gray-700">
        <h2 className="text-2xl font-bold mb-6 text-center">Login to DocuFlow</h2>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-200 p-3 rounded mb-4 text-sm text-center">
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin} className="space-y-4">
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

          <button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded font-semibold transition shadow-lg"
          >
            Sign In
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-400">
          New here? <Link href="/register" className="text-blue-400 hover:underline">Create an account</Link>
        </div>
      </div>
    </div>
  );
}