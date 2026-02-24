import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Common/Navbar';
import NotificationCenter from './components/Common/NotificationCenter';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import UserDashboard from './components/Dashboard/UserDashboard';
import FounderDashboard from './components/Dashboard/FounderDashboard';
import IdeaSubmission from './components/Project/IdeaSubmission';
import MatchList from './components/Matching/MatchList';
import ProfileEdit from './components/Profile/ProfileEdit';
import CollaborationRequests from './components/Collaboration/CollaborationRequests';
import LiveChat from './components/Chat/LiveChat';
import { getCurrentUser } from './utils/auth';
import { useWebSocket } from './utils/websocket';
import palette from './palette';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loaderText, setLoaderText] = useState('');
  const { connected, notifications, clearNotifications } = useWebSocket();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    const text = 'SCANNING THE TALENT POOL';
    let index = 0;
    const interval = setInterval(() => {
      index += 1;
      setLoaderText(text.slice(0, index));
      if (index >= text.length) clearInterval(interval);
    }, 60);

    return () => clearInterval(interval);
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

  const handleCloseNotification = (id) => {
    // Notification auto-removal is handled in the hook
  };

  if (loading) {
    return (
      <div className="cinematic-loader">
        <div style={{
          position: 'relative',
          zIndex: 3,
          display: 'grid',
          justifyItems: 'center',
          gap: palette.spacing.lg,
          textAlign: 'center',
        }}>
          <div className="pulse-ring" />
          <p style={{
            fontFamily: palette.typography.fontFamily.mono,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            fontSize: palette.typography.fontSize.xs,
            color: palette.colors.text.secondary,
          }}>
            {loaderText}
          </p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="app-shell" style={{ 
        minHeight: '100vh', 
        backgroundColor: palette.colors.background.primary 
      }}>
        {user && <Navbar user={user} onLogout={handleLogout} />}
        
        {/* WebSocket Notifications */}
        <NotificationCenter 
          notifications={notifications} 
          onClose={handleCloseNotification}
        />
        
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
            path="/profile/edit" 
            element={user ? <ProfileEdit user={user} onUpdate={checkAuth} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/requests" 
            element={user ? <CollaborationRequests user={user} onRequestUpdate={checkAuth} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/chat/:projectId" 
            element={user ? <LiveChat user={user} /> : <Navigate to="/login" />} 
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
        <footer style={{
          marginTop: palette.spacing['2xl'],
          borderTop: `1px solid ${palette.colors.border.primary}`,
          padding: `${palette.spacing.xl} ${palette.spacing.lg}`,
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute',
            left: '50%',
            bottom: '-160px',
            transform: 'translateX(-50%)',
            width: '560px',
            height: '260px',
            background: 'radial-gradient(circle, rgba(201,168,76,0.05) 0%, rgba(201,168,76,0) 70%)',
            pointerEvents: 'none',
          }} />
          <div style={{ position: 'relative', zIndex: 2 }}>
            <p className="mono-label" style={{ marginBottom: palette.spacing.xs }}>Founding Mindset</p>
            <p style={{ color: palette.colors.text.tertiary, fontSize: palette.typography.fontSize.xs }}>
              Copyright {new Date().getFullYear()} Founding Mindset. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
