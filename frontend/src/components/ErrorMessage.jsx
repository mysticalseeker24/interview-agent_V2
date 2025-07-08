const ErrorMessage = ({ 
  message, 
  title = 'Error', 
  type = 'error',
  onDismiss,
  className = '' 
}) => {
  const typeStyles = {
    error: {
      backgroundColor: '#fee2e2',
      color: '#dc2626',
      borderColor: '#fecaca'
    },
    warning: {
      backgroundColor: '#fef3c7',
      color: '#d97706',
      borderColor: '#fde68a'
    },
    info: {
      backgroundColor: '#dbeafe',
      color: '#2563eb',
      borderColor: '#bfdbfe'
    },
    success: {
      backgroundColor: '#d1fae5',
      color: '#059669',
      borderColor: '#a7f3d0'
    }
  };

  const containerStyle = {
    padding: '1rem',
    borderRadius: '8px',
    border: '1px solid',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.75rem',
    ...typeStyles[type]
  };

  const iconMap = {
    error: '⚠️',
    warning: '⚠️',
    info: 'ℹ️',
    success: '✅'
  };

  return (
    <div style={containerStyle} className={className}>
      <span style={{ fontSize: '16px', lineHeight: 1 }}>
        {iconMap[type]}
      </span>
      <div style={{ flex: 1 }}>
        {title && (
          <h4 style={{ 
            margin: '0 0 0.25rem 0', 
            fontSize: '14px', 
            fontWeight: '600' 
          }}>
            {title}
          </h4>
        )}
        <p style={{ 
          margin: 0, 
          fontSize: '14px', 
          lineHeight: '1.4' 
        }}>
          {message}
        </p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            fontSize: '16px',
            padding: '0',
            lineHeight: 1
          }}
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
