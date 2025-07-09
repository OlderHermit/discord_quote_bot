import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Approve from './pages/Approve';
import './styles/globals.css';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Public route - but redirect if already logged in */}
                <Route path="/login"
                    element={
                        <Login />
                    }
                />

                {/* Protected routes */}
                <Route path="/"
                    element={
                        <ProtectedRoute><Home /></ProtectedRoute>
                    }
                />

                <Route path="/approve"
                    element={
                        <ProtectedRoute requiredRole="master"><Approve /></ProtectedRoute>
                    }
                />
            </Routes>
        </BrowserRouter>
    );
}

export default App;