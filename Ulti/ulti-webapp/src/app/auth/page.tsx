'use client'

import { useState } from 'react'
import { createClient } from '@/utils/supabase/client'
import { useRouter } from 'next/navigation'

export default function AuthPage() {
    const [identifier, setIdentifier] = useState('') // Email or Username
    const [password, setPassword] = useState('')
    const [username, setUsername] = useState('') // Only for signup
    const [isSignUP, setIsSignUp] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const router = useRouter()
    const supabase = createClient()

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            if (isSignUP) {
                if (!username) throw new Error("Felhasználónév kötelező!")

                const { error: signUpError } = await supabase.auth.signUp({
                    email: identifier,
                    password,
                    options: {
                        data: { username }
                    }
                })
                if (signUpError) throw signUpError
                alert('Sikeres regisztráció! Jelentkezz be.')
                setIsSignUp(false)
            } else {
                let loginEmail = identifier

                // If the user didn't type an email address, treat it as a username
                if (!identifier.includes('@')) {
                    const { data, error: rpcError } = await supabase.rpc('get_email_by_username', { p_username: identifier })
                    if (rpcError || !data) {
                        throw new Error('Nem található ilyen felhasználónév, vagy hibás jelszó!')
                    }
                    loginEmail = data as string
                }

                const { error: signInError } = await supabase.auth.signInWithPassword({
                    email: loginEmail,
                    password,
                })
                if (signInError) throw signInError
                router.push('/dashboard')
                router.refresh()
            }
        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center p-4 bg-slate-50">
            <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-xl">
                <h1 className="text-3xl font-black text-center mb-8 text-slate-800">
                    Ulti <span className="text-red-600">Aréna</span>
                </h1>

                {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4">{error}</div>}

                <form onSubmit={handleAuth} className="space-y-4">
                    {isSignUP && (
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Játékosnév</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                                placeholder="pl. Pikk Dáma"
                            />
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            {isSignUP ? 'Email cím' : 'Email cím vagy Felhasználónév'}
                        </label>
                        <input
                            type={isSignUP ? "email" : "text"}
                            value={identifier}
                            onChange={(e) => setIdentifier(e.target.value)}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                            placeholder={isSignUP ? "hello@ulti.hu" : "Példa: Pikk Dáma"}
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Jelszó</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                            placeholder="••••••••"
                            required
                            minLength={6}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-lg transition-colors mt-4 disabled:opacity-50"
                    >
                        {loading ? 'Kérlek várj...' : (isSignUP ? 'Regisztráció' : 'Belépés')}
                    </button>
                </form>

                <p className="text-center text-sm mt-6 text-slate-600">
                    {isSignUP ? 'Már van fiókod?' : 'Nincs még fiókod?'}
                    <button
                        onClick={() => setIsSignUp(!isSignUP)}
                        className="ml-2 text-red-600 font-semibold hover:underline"
                        type="button"
                    >
                        {isSignUP ? 'Jelentkezz be!' : 'Regisztrálj!'}
                    </button>
                </p>
            </div>
        </div>
    )
}
