import { card } from '../styles';

const Card = ({ 
  children, 
  title, 
  subtitle,
  footer,
  onClick,
  hoverable = false,
  padding = 'normal',
  className = '',
  style = {}
}) => {
  const paddingMap = {
    none: { padding: 0 },
    small: { padding: '0.75rem' },
    normal: { padding: '1.5rem' },
    large: { padding: '2rem' }
  };

  const cardStyle = {
    ...card,
    ...paddingMap[padding],
    ...style,
    ...(onClick && { cursor: 'pointer' }),
    ...(hoverable && {
      transition: 'all 0.2s ease',
      ':hover': {
        transform: 'translateY(-2px)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
      }
    })
  };

  const titleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1f2937',
    margin: '0 0 0.5rem 0'
  };

  const subtitleStyle = {
    fontSize: '14px',
    color: '#6b7280',
    margin: '0 0 1rem 0'
  };

  const footerStyle = {
    marginTop: '1rem',
    paddingTop: '1rem',
    borderTop: '1px solid #e5e7eb'
  };

  return (
    <div 
      style={cardStyle} 
      className={className}
      onClick={onClick}
      onMouseEnter={hoverable ? (e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
      } : undefined}
      onMouseLeave={hoverable ? (e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
      } : undefined}
    >
      {title && (
        <h3 style={titleStyle}>
          {title}
        </h3>
      )}
      
      {subtitle && (
        <p style={subtitleStyle}>
          {subtitle}
        </p>
      )}
      
      <div>
        {children}
      </div>
      
      {footer && (
        <div style={footerStyle}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
