import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface Lesson {
    id: str;
    title: str;
    category: str;
    difficulty: str;
    duration_minutes: number;
}

export default function AcademyPage() {
    const [lessons, setLessons] = useState<Lesson[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLessons = async () => {
            try {
                const response = await api.get('/academy/lessons');
                setLessons(response.data);
            } catch (error) {
                console.error('Failed to fetch lessons', error);
            } finally {
                setLoading(false);
            }
        };

        fetchLessons();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 p-8 flex justify-center items-center">
                <div className="text-poker-gold text-xl">Loading Academy...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 p-8">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-4xl font-bold text-white mb-8">Academy</h1>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {lessons.map((lesson) => (
                        <Link
                            to={`/academy/lesson/${lesson.id}`}
                            key={lesson.id}
                            className="card group hover:border-poker-gold transition-all"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase
                  ${lesson.difficulty === 'beginner' ? 'bg-green-500/10 text-green-500' :
                                        lesson.difficulty === 'intermediate' ? 'bg-yellow-500/10 text-yellow-500' :
                                            'bg-red-500/10 text-red-500'}`}>
                                    {lesson.difficulty}
                                </span>
                                <span className="text-gray-400 text-sm flex items-center gap-1">
                                    ⏱️ {lesson.duration_minutes} min
                                </span>
                            </div>

                            <h3 className="text-xl font-bold text-white mb-2 group-hover:text-poker-gold transition-colors">
                                {lesson.title}
                            </h3>

                            <div className="text-gray-400 text-sm capitalize">
                                Category: {lesson.category}
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
