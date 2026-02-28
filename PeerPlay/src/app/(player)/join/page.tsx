import JoinSessionForm from '@/components/JoinSessionForm'
import Link from 'next/link'

export default function JoinPage() {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-8">
            <div className="bg-white p-12 rounded-2xl shadow-xl w-full max-w-lg border border-gray-100 flex flex-col items-center">

                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    Join Session
                </h1>
                <p className="text-gray-500 mb-8 text-center text-sm">
                    Enter the Session ID provided by your HR representative to enter the lobby.
                </p>

                <JoinSessionForm />

                <div className="mt-8 text-center text-sm text-gray-500 hover:text-gray-800">
                    <Link href="/">← Back to Home</Link>
                </div>
            </div>
        </div>
    )
}
