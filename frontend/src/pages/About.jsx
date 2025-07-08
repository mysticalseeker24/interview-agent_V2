import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import {
  container,
  card,
  primaryButton,
  secondaryButton,
  flexCenter,
  pageTitle,
  pageSubtitle,
  section,
  sectionTitle
} from '../styles';

const About = () => {
  const features = [
    {
      title: 'AI-Powered Interviews',
      description: 'Practice with realistic AI interviewers that adapt to your responses',
      icon: '🤖'
    },
    {
      title: 'Expert-Vetted Questions',
      description: 'Access thousands of questions used by top companies',
      icon: '❓'
    },
    {
      title: 'Real-time Feedback',
      description: 'Get instant analysis of your performance and areas for improvement',
      icon: '📊'
    },
    {
      title: 'Industry-Specific Modules',
      description: 'Specialized interview modules for different roles and industries',
      icon: '🎯'
    },
    {
      title: 'Progress Tracking',
      description: 'Monitor your improvement over time with detailed analytics',
      icon: '📈'
    },
    {
      title: 'Resume Integration',
      description: 'Upload your resume for personalized interview questions',
      icon: '📄'
    }
  ];

  const steps = [
    {
      step: '1',
      title: 'Choose Your Module',
      description: 'Select from our collection of interview modules tailored to specific roles and industries'
    },
    {
      step: '2', 
      title: 'Set Up Your Environment',
      description: 'Test your camera and microphone, upload your resume for personalized questions'
    },
    {
      step: '3',
      title: 'Practice Interview',
      description: 'Engage in realistic interview sessions with our AI interviewer'
    },
    {
      step: '4',
      title: 'Review & Improve',
      description: 'Get detailed feedback and analytics to identify areas for improvement'
    }
  ];

  const testimonials = [
    {
      name: 'Sarah Chen',
      role: 'Software Engineer at Google',
      content: 'TalentSync helped me prepare for technical interviews. The feedback was incredibly detailed and helped me land my dream job!'
    },
    {
      name: 'Michael Rodriguez',
      role: 'Product Manager at Meta',
      content: 'The industry-specific modules were perfect for PM interviews. I felt much more confident going into my interviews.'
    },
    {
      name: 'Emily Thompson',
      role: 'Data Scientist at Netflix',
      content: 'The AI interviewer asks follow-up questions just like real interviewers. It\'s the closest thing to the real experience.'
    }
  ];

  return (
    <>
      <PageHeader
        showNavigation={false}
        customActions={
          <>
            <Link to="/login" style={{ marginRight: '1rem' }}>Login</Link>
            <Link
              to="/signup"
              style={{
                ...primaryButton,
                padding: '0.5rem 1rem',
                fontSize: '14px',
                textDecoration: 'none'
              }}
            >
              Get Started
            </Link>
          </>
        }
      />

      {/* Hero Section */}
      <section style={{
        ...flexCenter,
        flexDirection: 'column',
        padding: '4rem 2rem',
        backgroundColor: '#f8fafc',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '800px' }}>
          <h1 style={{
            ...pageTitle,
            fontSize: '48px',
            marginBottom: '1rem'
          }}>
            Master Your Next Interview
          </h1>
          <p style={{
            ...pageSubtitle,
            fontSize: '20px',
            marginBottom: '2rem',
            lineHeight: '1.6'
          }}>
            Practice with AI-powered interview simulations, get real-time feedback, 
            and build the confidence you need to land your dream job.
          </p>
          <div style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <Link
              to="/signup"
              style={{
                ...primaryButton,
                padding: '1rem 2rem',
                fontSize: '16px',
                textDecoration: 'none'
              }}
            >
              Start Practicing Free
            </Link>
            <Link
              to="/login"
              style={{
                ...secondaryButton,
                padding: '1rem 2rem',
                fontSize: '16px',
                textDecoration: 'none'
              }}
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{ ...container, ...section }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={sectionTitle}>Why Choose TalentSync?</h2>
          <p style={pageSubtitle}>
            Everything you need to ace your interviews
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem'
        }}>
          {features.map((feature, index) => (
            <div key={index} style={{
              ...card,
              textAlign: 'center',
              padding: '2rem'
            }}>
              <div style={{
                fontSize: '48px',
                marginBottom: '1rem'
              }}>
                {feature.icon}
              </div>
              <h3 style={{
                fontSize: '20px',
                fontWeight: '600',
                marginBottom: '1rem',
                color: '#1f2937'
              }}>
                {feature.title}
              </h3>
              <p style={{
                color: '#6b7280',
                lineHeight: '1.6'
              }}>
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section style={{
        backgroundColor: '#f8fafc',
        padding: '4rem 0'
      }}>
        <div style={container}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 style={sectionTitle}>How It Works</h2>
            <p style={pageSubtitle}>
              Get started in just four simple steps
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '2rem'
          }}>
            {steps.map((step, index) => (
              <div key={index} style={{
                textAlign: 'center',
                position: 'relative'
              }}>
                {/* Step Number */}
                <div style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  ...flexCenter,
                  fontSize: '24px',
                  fontWeight: '700',
                  margin: '0 auto 1.5rem auto'
                }}>
                  {step.step}
                </div>

                {/* Step Content */}
                <h3 style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  marginBottom: '1rem',
                  color: '#1f2937'
                }}>
                  {step.title}
                </h3>
                <p style={{
                  color: '#6b7280',
                  lineHeight: '1.6'
                }}>
                  {step.description}
                </p>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div style={{
                    position: 'absolute',
                    top: '30px',
                    right: '-50%',
                    width: '100%',
                    height: '2px',
                    backgroundColor: '#e5e7eb',
                    zIndex: -1
                  }}>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section style={{ ...container, ...section }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={sectionTitle}>What Our Users Say</h2>
          <p style={pageSubtitle}>
            Join thousands of professionals who've improved their interview skills
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem'
        }}>
          {testimonials.map((testimonial, index) => (
            <div key={index} style={{
              ...card,
              padding: '2rem'
            }}>
              <p style={{
                fontSize: '16px',
                lineHeight: '1.6',
                marginBottom: '1.5rem',
                color: '#374151',
                fontStyle: 'italic'
              }}>
                "{testimonial.content}"
              </p>
              <div>
                <div style={{
                  fontWeight: '600',
                  color: '#1f2937',
                  marginBottom: '0.25rem'
                }}>
                  {testimonial.name}
                </div>
                <div style={{
                  fontSize: '14px',
                  color: '#6b7280'
                }}>
                  {testimonial.role}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Stats Section */}
      <section style={{
        backgroundColor: '#2563eb',
        color: '#ffffff',
        padding: '4rem 0'
      }}>
        <div style={container}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '2rem',
            textAlign: 'center'
          }}>
            <div>
              <div style={{
                fontSize: '48px',
                fontWeight: '700',
                marginBottom: '0.5rem'
              }}>
                50K+
              </div>
              <div style={{ fontSize: '18px', opacity: 0.9 }}>
                Interviews Completed
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '48px',
                fontWeight: '700',
                marginBottom: '0.5rem'
              }}>
                95%
              </div>
              <div style={{ fontSize: '18px', opacity: 0.9 }}>
                Success Rate
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '48px',
                fontWeight: '700',
                marginBottom: '0.5rem'
              }}>
                200+
              </div>
              <div style={{ fontSize: '18px', opacity: 0.9 }}>
                Interview Modules
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '48px',
                fontWeight: '700',
                marginBottom: '0.5rem'
              }}>
                24/7
              </div>
              <div style={{ fontSize: '18px', opacity: 0.9 }}>
                Available Practice
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{
        ...flexCenter,
        flexDirection: 'column',
        padding: '4rem 2rem',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '600px' }}>
          <h2 style={{
            fontSize: '36px',
            fontWeight: '700',
            marginBottom: '1rem',
            color: '#1f2937'
          }}>
            Ready to Ace Your Next Interview?
          </h2>
          <p style={{
            ...pageSubtitle,
            fontSize: '18px',
            marginBottom: '2rem'
          }}>
            Join thousands of professionals who've already improved their interview skills with TalentSync.
          </p>
          <Link
            to="/signup"
            style={{
              ...primaryButton,
              padding: '1rem 2rem',
              fontSize: '16px',
              textDecoration: 'none'
            }}
          >
            Get Started Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        backgroundColor: '#1f2937',
        color: '#ffffff',
        padding: '3rem 0 2rem 0'
      }}>
        <div style={container}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '2rem',
            marginBottom: '2rem'
          }}>
            <div>
              <div style={{
                fontSize: '24px',
                fontWeight: '700',
                marginBottom: '1rem'
              }}>
                TalentSync
              </div>
              <p style={{
                color: '#9ca3af',
                lineHeight: '1.6'
              }}>
                The leading platform for AI-powered interview practice. 
                Master your skills and land your dream job.
              </p>
            </div>
            <div>
              <h4 style={{
                fontSize: '18px',
                fontWeight: '600',
                marginBottom: '1rem'
              }}>
                Platform
              </h4>
              <ul style={{
                listStyle: 'none',
                padding: 0,
                margin: 0
              }}>
                <li style={{ marginBottom: '0.5rem' }}>
                  <Link to="/signup" style={{ color: '#9ca3af', textDecoration: 'none' }}>
                    Get Started
                  </Link>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <Link to="/login" style={{ color: '#9ca3af', textDecoration: 'none' }}>
                    Sign In
                  </Link>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <Link to="/about" style={{ color: '#9ca3af', textDecoration: 'none' }}>
                    About
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 style={{
                fontSize: '18px',
                fontWeight: '600',
                marginBottom: '1rem'
              }}>
                Support
              </h4>
              <ul style={{
                listStyle: 'none',
                padding: 0,
                margin: 0
              }}>
                <li style={{ marginBottom: '0.5rem' }}>
                  <a href="mailto:support@talentsync.com" style={{ color: '#9ca3af', textDecoration: 'none' }}>
                    Contact Us
                  </a>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <a href="#" style={{ color: '#9ca3af', textDecoration: 'none' }}>
                    Help Center
                  </a>
                </li>
                <li style={{ marginBottom: '0.5rem' }}>
                  <a href="#" style={{ color: '#9ca3af', textDecoration: 'none' }}>
                    Privacy Policy
                  </a>
                </li>
              </ul>
            </div>
          </div>
          
          <div style={{
            borderTop: '1px solid #374151',
            paddingTop: '2rem',
            textAlign: 'center'
          }}>
            <p style={{ color: '#9ca3af' }}>
              © 2024 TalentSync. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </>
  );
};

export default About;
