import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-white relative overflow-hidden">
      
      {/* Background Design */}
      <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full blur-[128px]"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500 rounded-full blur-[128px]"></div>
      </div>

      <div className="z-10 text-center max-w-3xl px-6">
        <div className="mb-6 inline-block px-4 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 text-sm font-medium">
          Secure Microservices Architecture
        </div>
        
        <h1 className="text-6xl text-yellow-300 font-bold mb-6 tracking-tight">
          Docu<span className="text-blue-500">Flow</span>
        </h1>
        
        <p className="text-xl text-gray-400 mb-10 leading-relaxed">
          Enterprise-grade document processing pipeline. 
          Built with <span className="text-white font-semibold">Zero-Trust Security</span>, 
          automated sanitization, and scalable microservices.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/login" className="px-8 py-4 bg-blue-600 rounded-lg hover:bg-blue-700 font-semibold transition shadow-lg hover:shadow-blue-500/25">
  Login
</Link>
          <Link 
            href="/register" 
            className="px-8 py-4 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 font-semibold transition"
          >
            Create Account
          </Link>
        </div>
      </div>

      {/* Footer / Tech Stack Badges */}
      <div className="absolute bottom-10 text-gray-500 text-sm flex gap-6 uppercase tracking-widest font-mono">
        <span>Docker</span>
        <span>•</span>
        <span>Kubernetes</span>
        <span>•</span>
        <span>Next.js</span>
        <span>•</span>
        <span>Python</span>
      </div>
    </main>
  );
}