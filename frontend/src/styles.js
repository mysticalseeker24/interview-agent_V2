// Global styles for TalentSync frontend
export const container = {
  padding: '1rem',
  maxWidth: '1200px',
  margin: '0 auto',
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif"
};

export const card = {
  padding: '1.5rem',
  border: '1px solid #e5e7eb',
  borderRadius: '12px',
  margin: '0.5rem',
  backgroundColor: '#ffffff',
  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
  transition: 'box-shadow 0.2s, transform 0.2s'
};

export const button = {
  padding: '0.75rem 1.5rem',
  cursor: 'pointer',
  border: 'none',
  borderRadius: '8px',
  fontSize: '14px',
  fontWeight: '500',
  transition: 'all 0.2s',
  fontFamily: 'inherit'
};

export const primaryButton = {
  ...button,
  backgroundColor: '#2563eb',
  color: '#ffffff'
};

export const secondaryButton = {
  ...button,
  backgroundColor: '#f3f4f6',
  color: '#374151',
  border: '1px solid #d1d5db'
};

export const input = {
  padding: '0.75rem',
  border: '1px solid #d1d5db',
  borderRadius: '6px',
  fontSize: '14px',
  width: '100%',
  fontFamily: 'inherit',
  transition: 'border-color 0.2s'
};

export const formGroup = {
  marginBottom: '1rem'
};

export const label = {
  display: 'block',
  marginBottom: '0.5rem',
  fontSize: '14px',
  fontWeight: '500',
  color: '#374151'
};

export const errorText = {
  color: '#dc2626',
  fontSize: '12px',
  marginTop: '0.25rem'
};

export const successText = {
  color: '#059669',
  fontSize: '12px',
  marginTop: '0.25rem'
};

export const flexCenter = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
};

export const flexBetween = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between'
};

export const grid = {
  display: 'grid',
  gap: '1rem'
};

export const gridResponsive = {
  ...grid,
  gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))'
};

export const badge = {
  padding: '0.25rem 0.75rem',
  borderRadius: '9999px',
  fontSize: '12px',
  fontWeight: '500'
};

export const badgeSuccess = {
  ...badge,
  backgroundColor: '#dcfce7',
  color: '#166534'
};

export const badgeWarning = {
  ...badge,
  backgroundColor: '#fef3c7',
  color: '#92400e'
};

export const badgeError = {
  ...badge,
  backgroundColor: '#fee2e2',
  color: '#991b1b'
};

export const badgeInfo = {
  ...badge,
  backgroundColor: '#dbeafe',
  color: '#1e40af'
};

export const header = {
  borderBottom: '1px solid #e5e7eb',
  backgroundColor: '#ffffff',
  padding: '1rem 0'
};

export const nav = {
  ...flexBetween,
  ...container
};

export const logo = {
  fontSize: '24px',
  fontWeight: '700',
  color: '#1f2937'
};

export const navLinks = {
  display: 'flex',
  gap: '2rem',
  alignItems: 'center'
};

export const navLink = {
  color: '#6b7280',
  textDecoration: 'none',
  fontSize: '14px',
  fontWeight: '500',
  transition: 'color 0.2s'
};

export const modal = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000
};

export const modalContent = {
  backgroundColor: '#ffffff',
  borderRadius: '12px',
  padding: '2rem',
  maxWidth: '500px',
  width: '90%',
  maxHeight: '90vh',
  overflow: 'auto'
};

export const loading = {
  ...flexCenter,
  padding: '2rem',
  color: '#6b7280'
};

export const pageTitle = {
  fontSize: '32px',
  fontWeight: '700',
  color: '#1f2937',
  marginBottom: '0.5rem'
};

export const pageSubtitle = {
  fontSize: '16px',
  color: '#6b7280',
  marginBottom: '2rem'
};

export const section = {
  marginBottom: '3rem'
};

export const sectionTitle = {
  fontSize: '20px',
  fontWeight: '600',
  color: '#1f2937',
  marginBottom: '1rem'
};
