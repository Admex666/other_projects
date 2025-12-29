import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function OnboardingPage() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        skill_level: 'beginner',
        game_format: 'cash',
        game_variant: 'nlh',
        player_goal: 'hobby_to_winning',
        current_bankroll: '',
        target_bankroll: '',
        weekly_hours: ''
    });

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const payload = {
                ...formData,
                current_bankroll: formData.current_bankroll ? parseFloat(formData.current_bankroll) : null,
                target_bankroll: formData.target_bankroll ? parseFloat(formData.target_bankroll) : null,
                weekly_hours: formData.weekly_hours ? parseFloat(formData.weekly_hours) : null,
            };

            await api.post('/onboarding/complete', payload);
            navigate('/dashboard');
        } catch (error) {
            console.error('Onboarding failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-poker-green-dark p-4">
            <div className="max-w-3xl mx-auto py-12">
                <div className="text-center mb-12">
                    <h1 className="text-5xl font-bold bg-gradient-to-r from-poker-gold to-poker-gold-light bg-clip-text text-transparent mb-4">
                        Welcome to PokerPro
                    </h1>
                    <p className="text-xl text-gray-300">Let's personalize your learning journey</p>
                </div>

                <div className="card-glass">
                    {/* Progress bar */}
                    <div className="mb-8">
                        <div className="flex justify-between mb-2">
                            <span className="text-sm text-gray-400">Step {step} of 3</span>
                            <span className="text-sm text-gray-400">{Math.round((step / 3) * 100)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                            <div
                                className="bg-gradient-to-r from-poker-green to-poker-gold h-2 rounded-full transition-all duration-300"
                                style={{ width: `${(step / 3) * 100}%` }}
                            />
                        </div>
                    </div>

                    {/* Step 1: Skill Level */}
                    {step === 1 && (
                        <div className="space-y-6">
                            <h2 className="text-2xl font-bold text-white mb-6">What's your current skill level?</h2>

                            <div className="grid gap-4">
                                {[
                                    { value: 'beginner', label: 'Beginner', desc: 'Just starting out or learning basics' },
                                    { value: 'intermediate', label: 'Intermediate', desc: 'Understand fundamentals, working on strategy' },
                                    { value: 'advanced', label: 'Advanced', desc: 'Experienced player, refining skills' }
                                ].map((option) => (
                                    <button
                                        key={option.value}
                                        onClick={() => setFormData({ ...formData, skill_level: option.value })}
                                        className={`p-6 rounded-xl border-2 text-left transition-all ${formData.skill_level === option.value
                                                ? 'border-poker-gold bg-poker-gold/10'
                                                : 'border-gray-700 hover:border-gray-600'
                                            }`}
                                    >
                                        <div className="font-semibold text-lg text-white">{option.label}</div>
                                        <div className="text-gray-400 text-sm mt-1">{option.desc}</div>
                                    </button>
                                ))}
                            </div>

                            <button onClick={() => setStep(2)} className="btn-primary w-full mt-8">
                                Continue
                            </button>
                        </div>
                    )}

                    {/* Step 2: Game Format */}
                    {step === 2 && (
                        <div className="space-y-6">
                            <h2 className="text-2xl font-bold text-white mb-6">What format do you play?</h2>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-3">Game Format</label>
                                <div className="grid grid-cols-2 gap-4">
                                    {[
                                        { value: 'cash', label: 'Cash Games' },
                                        { value: 'mtt', label: 'Tournaments (MTT)' },
                                        { value: 'sng', label: 'Sit & Go' },
                                        { value: 'spin_and_go', label: 'Spin & Go' }
                                    ].map((option) => (
                                        <button
                                            key={option.value}
                                            onClick={() => setFormData({ ...formData, game_format: option.value })}
                                            className={`p-4 rounded-lg border-2 transition-all ${formData.game_format === option.value
                                                    ? 'border-poker-gold bg-poker-gold/10'
                                                    : 'border-gray-700 hover:border-gray-600'
                                                }`}
                                        >
                                            <div className="font-semibold text-white">{option.label}</div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-3">Game Variant</label>
                                <div className="grid grid-cols-2 gap-4">
                                    {[
                                        { value: 'nlh', label: 'No-Limit Hold\'em' },
                                        { value: 'plo', label: 'Pot-Limit Omaha' }
                                    ].map((option) => (
                                        <button
                                            key={option.value}
                                            onClick={() => setFormData({ ...formData, game_variant: option.value })}
                                            className={`p-4 rounded-lg border-2 transition-all ${formData.game_variant === option.value
                                                    ? 'border-poker-gold bg-poker-gold/10'
                                                    : 'border-gray-700 hover:border-gray-600'
                                                }`}
                                        >
                                            <div className="font-semibold text-white">{option.label}</div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="flex gap-4 mt-8">
                                <button onClick={() => setStep(1)} className="btn-secondary flex-1">
                                    Back
                                </button>
                                <button onClick={() => setStep(3)} className="btn-primary flex-1">
                                    Continue
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Goals */}
                    {step === 3 && (
                        <div className="space-y-6">
                            <h2 className="text-2xl font-bold text-white mb-6">What are your goals?</h2>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-3">Player Goal</label>
                                <div className="grid gap-3">
                                    {[
                                        { value: 'hobby_to_winning', label: 'Hobby → Winning Player' },
                                        { value: 'semi_pro', label: 'Semi-Professional' },
                                        { value: 'professional', label: 'Professional' },
                                        { value: 'high_stakes', label: 'High Stakes Pro' }
                                    ].map((option) => (
                                        <button
                                            key={option.value}
                                            onClick={() => setFormData({ ...formData, player_goal: option.value })}
                                            className={`p-4 rounded-lg border-2 text-left transition-all ${formData.player_goal === option.value
                                                    ? 'border-poker-gold bg-poker-gold/10'
                                                    : 'border-gray-700 hover:border-gray-600'
                                                }`}
                                        >
                                            <div className="font-semibold text-white">{option.label}</div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Current Bankroll ($)
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.current_bankroll}
                                        onChange={(e) => setFormData({ ...formData, current_bankroll: e.target.value })}
                                        className="input-field"
                                        placeholder="500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Target Bankroll ($)
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.target_bankroll}
                                        onChange={(e) => setFormData({ ...formData, target_bankroll: e.target.value })}
                                        className="input-field"
                                        placeholder="5000"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Weekly Study Hours
                                </label>
                                <input
                                    type="number"
                                    value={formData.weekly_hours}
                                    onChange={(e) => setFormData({ ...formData, weekly_hours: e.target.value })}
                                    className="input-field"
                                    placeholder="10"
                                />
                            </div>

                            <div className="flex gap-4 mt-8">
                                <button onClick={() => setStep(2)} className="btn-secondary flex-1">
                                    Back
                                </button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={loading}
                                    className="btn-primary flex-1 disabled:opacity-50"
                                >
                                    {loading ? 'Completing...' : 'Complete Setup'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
