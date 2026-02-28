import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-8">
      <div className="bg-white p-12 rounded-2xl shadow-xl w-full max-w-lg text-center">
        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 mb-4">
          PeerPlay MVP
        </h1>
        <p className="text-gray-600 mb-10 text-lg">
          Behavioral Simulation-Based Organizational Diagnostics Platform
        </p>

        <div className="space-y-4">
          <Link href="/dashboard" className="block w-full text-center hover:scale-105 transition-transform">
            <div className="bg-indigo-600 text-white rounded-xl p-4 font-semibold text-xl shadow-md hover:bg-indigo-700">
              HR Dashboard 🏢
            </div>
            <p className="text-sm text-gray-500 mt-2">Manage sessions, view networks, and analytics</p>
          </Link>

          <div className="relative py-4 flex items-center">
            <div className="flex-grow border-t border-gray-300"></div>
            <span className="flex-shrink-0 mx-4 text-gray-400">or</span>
            <div className="flex-grow border-t border-gray-300"></div>
          </div>

          <Link href="/join" className="block w-full text-center hover:scale-105 transition-transform">
            <div className="bg-white text-indigo-600 border-2 border-indigo-600 rounded-xl p-4 font-semibold text-xl shadow-sm hover:bg-indigo-50">
              Player Join 🎮
            </div>
            <p className="text-sm text-gray-500 mt-2">Join an active session as a participant</p>
          </Link>
        </div>
      </div>
    </div>
  )
}
