import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

interface QuizQuestion {
    id: string;
    question: string;
    options: string[];
    correct: string;
}

interface Lesson {
    id: string;
    title: string;
    content: string;
    quiz_questions?: QuizQuestion[];
}

export default function LessonPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [lesson, setLesson] = useState<Lesson | null>(null);
    const [loading, setLoading] = useState(true);
    const [completed, setCompleted] = useState(false);

    useEffect(() => {
        const fetchLesson = async () => {
            try {
                const response = await api.get(`/academy/lessons/${id}`);
                setLesson(response.data);
            } catch (error) {
                console.error('Failed to fetch lesson', error);
            } finally {
                setLoading(false);
            }
        };

        fetchLesson();
    }, [id]);

    const handleComplete = async () => {
        try {
            await api.post('/academy/progress', {
                lesson_id: id,
                completed: true,
                time_spent_minutes: 10 // TODO: Track actual time
            });
            setCompleted(true);
            // Optional: Add gamification feedback here
        } catch (error) {
            console.error('Failed to update progress', error);
        }
    };

    if (loading) return <div className="p-8 text-white">Loading lesson...</div>;
    if (!lesson) return <div className="p-8 text-white">Lesson not found</div>;

    return (
        <div className="min-h-screen bg-gray-900 p-8">
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => navigate('/academy')}
                    className="text-gray-400 hover:text-white mb-6 flex items-center gap-2"
                >
                    ← Back to Academy
                </button>

                <article className="card prose prose-invert max-w-none">
                    <h1 className="text-4xl font-bold text-poker-gold mb-6">{lesson.title}</h1>

                    <div className="markdown-content">
                        <ReactMarkdown>{lesson.content}</ReactMarkdown>
                    </div>

                    <div className="mt-12 pt-8 border-t border-gray-700 flex justify-between items-center">
                        <div className="text-gray-400">
                            {completed ? '✅ Lesson Completed' : 'Read through carefully to complete'}
                        </div>

                        {!completed && (
                            <button
                                onClick={handleComplete}
                                className="btn-primary"
                            >
                                Mark as Completed
                            </button>
                        )}

                        {completed && (
                            <button
                                onClick={() => navigate('/academy')}
                                className="btn-secondary"
                            >
                                Next Lesson →
                            </button>
                        )}
                    </div>
                </article>
            </div>
        </div>
    );
}
