import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Button from './Button';
import palette from '../../palette';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    handleScroll();
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 900);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  const navItems = [
    { label: 'Requests', path: '/requests' },
    { label: 'Edit Profile', path: '/profile/edit' },
  ];

  const isActive = (path) => location.pathname.startsWith(path);

  return (
    <nav style={{
      backgroundColor: scrolled ? 'rgba(0,0,0,0.8)' : 'transparent',
      backdropFilter: scrolled ? 'blur(20px)' : 'none',
      borderBottom: `1px solid ${scrolled ? palette.colors.border.primary : 'transparent'}`,
      padding: `${palette.spacing.md} ${palette.spacing.xl}`,
      position: 'sticky',
      top: 0,
      zIndex: palette.zIndex.sticky,
      transition: `all ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: 'auto 1fr auto',
        alignItems: 'center',
        gap: palette.spacing.lg,
      }}>
        <Link
          to="/dashboard"
          style={{
            fontFamily: palette.typography.fontFamily.display,
            fontSize: 'clamp(1.6rem, 2.2vw, 2.2rem)',
            letterSpacing: '0.07em',
            color: palette.colors.text.primary,
            textDecoration: 'none',
            textTransform: 'uppercase',
            lineHeight: 0.9,
          }}
        >
          Founding
          <br />
          Mindset
        </Link>

        {!isMobile && (
          <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: palette.spacing.lg,
        }}>
          {navItems.map((item) => (
            <button
              key={item.path}
              type="button"
              onClick={() => navigate(item.path)}
              style={{
                background: 'transparent',
                border: 'none',
                color: palette.colors.text.secondary,
                fontFamily: palette.typography.fontFamily.primary,
                fontSize: palette.typography.fontSize.xs,
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                padding: `${palette.spacing.xs} 0`,
                position: 'relative',
                transition: `color ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
              }}
            >
              {item.label}
              <span style={{
                position: 'absolute',
                left: 0,
                bottom: '-4px',
                width: '100%',
                height: '1px',
                backgroundColor: palette.colors.primary.cyan,
                transform: isActive(item.path) ? 'scaleX(1)' : 'scaleX(0)',
                transformOrigin: 'left',
                transition: `transform ${palette.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
              }} />
            </button>
          ))}
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: palette.spacing.md }}>
          <div style={{
            display: isMobile ? 'none' : 'flex',
            alignItems: 'center',
            gap: palette.spacing.md,
          }}>
            <span style={{
              color: palette.colors.text.secondary,
              fontSize: palette.typography.fontSize.sm,
            }}>
              {user.name}
            </span>
            <span style={{
              border: `1px solid ${palette.colors.border.primary}`,
              color: palette.colors.primary.cyan,
              padding: `${palette.spacing.xs} ${palette.spacing.md}`,
              borderRadius: palette.borderRadius.full,
              fontSize: palette.typography.fontSize.xs,
              letterSpacing: '0.16em',
              textTransform: 'uppercase',
            }}>
              {user.role}
            </span>
          </div>

          <Button onClick={handleLogout} variant="secondary" size="sm">
            Logout
          </Button>

          {isMobile && (
            <button
              type="button"
              aria-label="Toggle menu"
              onClick={() => setMobileOpen((prev) => !prev)}
              style={{
                background: 'transparent',
                border: `1px solid ${palette.colors.border.primary}`,
                color: palette.colors.text.primary,
                padding: palette.spacing.sm,
                borderRadius: palette.borderRadius.md,
                fontFamily: palette.typography.fontFamily.primary,
                fontSize: palette.typography.fontSize.xs,
                letterSpacing: '0.18em',
                textTransform: 'uppercase',
              }}
            >
              Menu
            </button>
          )}
        </div>
      </div>

      {mobileOpen && (
        <div style={{
          marginTop: palette.spacing.md,
          borderTop: `1px solid ${palette.colors.border.primary}`,
          paddingTop: palette.spacing.md,
          display: 'grid',
          gap: palette.spacing.sm,
        }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
              variant={isActive(item.path) ? 'primary' : 'secondary'}
              size="sm"
              fullWidth
            >
              {item.label}
            </Button>
          ))}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
