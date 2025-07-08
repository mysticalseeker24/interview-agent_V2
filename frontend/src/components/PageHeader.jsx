import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  header, 
  nav, 
  logo, 
  navLinks, 
  navLink, 
  secondaryButton 
} from '../styles';

const PageHeader = ({ showNavigation = true, customActions }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigationItems = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Profile', path: '/profile' },
    { label: 'About', path: '/about' }
  ];

  return (
    <header style={header}>
      <nav style={nav}>
        <div style={logo} onClick={() => navigate('/dashboard')}>
          TalentSync
        </div>
        
        {showNavigation && (
          <div style={navLinks}>
            {navigationItems.map((item) => (
              <a
                key={item.path}
                href={item.path}
                style={navLink}
                onClick={(e) => {
                  e.preventDefault();
                  navigate(item.path);
                }}
              >
                {item.label}
              </a>
            ))}
            
            {customActions}
            
            {user && (
              <>
                <span style={{ 
                  color: '#6b7280', 
                  fontSize: '14px',
                  marginRight: '1rem'
                }}>
                  Welcome, {user.full_name}
                </span>
                <button
                  onClick={handleLogout}
                  style={{
                    ...secondaryButton,
                    padding: '0.5rem 1rem',
                    fontSize: '12px'
                  }}
                >
                  Logout
                </button>
              </>
            )}
          </div>
        )}
      </nav>
    </header>
  );
};

export default PageHeader;
