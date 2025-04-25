import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/LoginPage.css'; 

const ForgotPassword: React.FC = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    // Function to validate email format
    const validateEmail = (email: string) => {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    };

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if(!validateEmail(email)) {
            setError('Please enter a valid email address');
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            // Send password reset request to the server
            const response = await fetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/reset-password?email=${encodeURIComponent(email)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to request password reset');
            }

            setSuccessMessage("We've sent a password reset link to your email address. Please check your inbox.");
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to request password reset');
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="login-page">
            <div className="form-container">
                <h1>Job Aggregator Platform</h1>
                <h2>Reset Password</h2>
                
                {successMessage ? (
                    <div className="success-message">
                        <div className="success-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                            </svg>
                            <span>Email sent</span>
                        </div>
                        <p>We've sent a password reset link to your email address. Please check your inbox.</p>
                        <button 
                            onClick={() => navigate('/login')}
                            className="submit-button"
                        >
                            Back to Login
                        </button>
                    </div>
                ) : (
                    <>
                        <p>Enter your email address and we'll send you a link to reset your password.</p>
                        <form onSubmit={handleSubmit}>
                            <div className="input-group">
                                <label htmlFor="email">Email</label>
                                <input
                                    type="email"
                                    id="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Enter your email"
                                    required
                                />
                            </div>
                            
                            {error && <div className="error-message">{error}</div>}
                            
                            <button
                                type="submit"
                                disabled={isLoading || !email}
                                className={`submit-button ${isLoading || !email ? 'disabled' : ''}`}
                            >
                                {isLoading ? 'Sending...' : 'Send Reset Link'}
                            </button>
                        </form>
                        <div className="back-link">
                            <a href="/login">Back to Login</a>
                        </div>
                    </>
                )}
            </div>
            <div className="image-container">
                <div className="reset-info">
                    <h3>Password Recovery</h3>
                    <p>We'll help you get back into your account</p>
                </div>
            </div>
        </div>
    );
}

export default ForgotPassword;