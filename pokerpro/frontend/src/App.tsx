import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import OnboardingPage from './pages/OnboardingPage';
import AcademyPage from './pages/AcademyPage';
import LessonPage from './pages/LessonPage';
import GTOPracticePage from './pages/GTOPracticePage';
import HandAnalyzerPage from './pages/HandAnalyzerPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                <Route
                    path="/onboarding"
                    element={
                        <ProtectedRoute>
                            <OnboardingPage />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <DashboardPage />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/academy"
                    element={
                        <ProtectedRoute>
                            <AcademyPage />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/academy/lesson/:id"
                    element={
                        <ProtectedRoute>
                            <LessonPage />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/gto-practice"
                    element={
                        <ProtectedRoute>
                            <GTOPracticePage />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/hand-analyzer"
                    element={
                        <ProtectedRoute>
                            <HandAnalyzerPage />
                        </ProtectedRoute>
                    }
                />

                <Route path="/" element={<Navigate to="/dashboard" />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
