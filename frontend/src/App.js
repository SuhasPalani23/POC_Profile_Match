import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Common/Navbar';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import UserDashboard from './components/Dashboard/UserDashboard';
import FounderDashboard from './components/Dashboard/FounderDashboard';
import IdeaSubmission from './components/Project/IdeaSubmission';
import MatchList from './components/Matching/MatchList';
import { getCurrentUser } from './utils/auth';
import palette from './palette';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: palette.colors.background.primary,
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          border: `4px solid ${palette.colors.border.primary}`,
          borderTop: `4px solid ${palette.colors.primary.cyan}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}></div>
      </div>
    );
  }

  return (
    <Router>
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: palette.colors.background.primary 
      }}>
        {user && <Navbar user={user} onLogout={handleLogout} />}
        <Routes>
          <Route 
            path="/login" 
            element={user ? <Navigate to="/dashboard" /> : <Login onLogin={checkAuth} />} 
          />
          <Route 
            path="/signup" 
            element={user ? <Navigate to="/dashboard" /> : <Signup onSignup={checkAuth} />} 
          />
          <Route 
            path="/dashboard" 
            element={
              user ? (
                user.role === 'founder' ? 
                  <FounderDashboard user={user} /> : 
                  <UserDashboard user={user} />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/submit-idea" 
            element={user ? <IdeaSubmission user={user} onSubmit={checkAuth} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/matches/:projectId" 
            element={user ? <MatchList user={user} /> : <Navigate to="/login" />} 
          />
          <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;