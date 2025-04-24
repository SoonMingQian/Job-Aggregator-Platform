import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/LoginPage.css'; // Reuse login page styles

const ResetPasswordPage: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [token, setToken] = useState('');
    const [email, setEmail] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [formErrors, setFormErrors] = useState({
        password: '',
        confirmPassword: ''
    });
    const [successMessage, setSuccessMessage] = useState('');

    useEffect(() => {
        // Extract token from URL query parameters
        const queryParams = new URLSearchParams(location.search);
        const tokenParam = queryParams.get('token');
        if (tokenParam) {
            setToken(tokenParam);
        } else {
            setError('Invalid or missing reset token');
        }
    }, [location]);

    // Password validation function - matches SignupPage
    const validatePassword = (password: string) => {
        if (!password) {
            setFormErrors(prev => ({ ...prev, password: 'Password is required' }));
            return false;
        }
        if (password.length < 8) {
            setFormErrors(prev => ({ ...prev, password: 'Password must be at least 8 characters' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, password: '' }));
        return true;
    }

    // Confirm password validation - matches SignupPage
    const validateConfirmPassword = (confirmPassword: string) => {
        if (confirmPassword !== newPassword) {
            setFormErrors(prev => ({ ...prev, confirmPassword: 'Passwords do not match' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, confirmPassword: '' }));
        return true;
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        
        switch(name) {
            case 'email':
                setEmail(value);
                break;
            case 'newPassword':
                setNewPassword(value);
                validatePassword(value);
                // Also validate confirm password if it's already entered
                if (confirmPassword) {
                    validateConfirmPassword(confirmPassword);
                }
                break;
            case 'confirmPassword':
                setConfirmPassword(value);
                validateConfirmPassword(value);
                break;
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        
        // Validate both password fields
        const isPasswordValid = validatePassword(newPassword);
        const isConfirmPasswordValid = validateConfirmPassword(confirmPassword);
        
        if (!isPasswordValid || !isConfirmPasswordValid) {
            return;
        }

        if (!token) {
            setError('Invalid reset token');
            return;
        }

        setIsLoading(true);
        
        try {
            const response = await fetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/savePassword`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token,
                    email,
                    newPassword: newPassword
                })
            });

            if (response.status === 400) {
                throw new Error('Invalid or expired token. Please request a new password reset.');
            } else if (response.status === 404) {
                throw new Error('Account not found. Please check your email address.');
            } else if (!response.ok) {
                const errorData = await response.text();
                throw new Error(errorData || 'Failed to reset password');
            }

            setSuccessMessage('Your password has been successfully reset. You can now login with your new password.');
            setTimeout(() => {
                navigate('/login');
            }, 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to reset password');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="form-container">
                <h1>Job Aggregator Platform</h1>
                <h2>Set New Password</h2>
                
                {successMessage ? (
                    <div className="success-message">
                        <p>{successMessage}</p>
                        <p>Redirecting to login page...</p>
                    </div>
                ) : (
                    <>
                        <form onSubmit={handleSubmit}>
                            <div className="input-group">
                                <label htmlFor="email">Email</label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={email}
                                    onChange={handleInputChange}
                                    placeholder="Enter your email"
                                    required
                                />
                            </div>
                            <div className="input-group">
                                <label htmlFor="newPassword">New Password</label>
                                <input
                                    type="password"
                                    id="newPassword"
                                    name="newPassword"
                                    value={newPassword}
                                    onChange={handleInputChange}
                                    placeholder="Enter new password"
                                    required
                                    className={formErrors.password ? 'error' : ''}
                                />
                                {formErrors.password && (
                                    <span className="error-text">{formErrors.password}</span>
                                )}
                            </div>
                            <div className="input-group">
                                <label htmlFor="confirmPassword">Confirm Password</label>
                                <input
                                    type="password"
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    value={confirmPassword}
                                    onChange={handleInputChange}
                                    placeholder="Confirm new password"
                                    required
                                    className={formErrors.confirmPassword ? 'error' : ''}
                                />
                                {formErrors.confirmPassword && (
                                    <span className="error-text">{formErrors.confirmPassword}</span>
                                )}
                            </div>
                            
                            {error && <div className="error-message">{error}</div>}
                            
                            <button
                                type="submit"
                                disabled={isLoading || !email || !newPassword || !confirmPassword || 
                                         !!formErrors.password || !!formErrors.confirmPassword}
                                className={`submit-button ${
                                    isLoading || !email || !newPassword || !confirmPassword || 
                                    !!formErrors.password || !!formErrors.confirmPassword ? 'disabled' : ''
                                }`}
                            >
                                {isLoading ? (
                                    <div className="spinner"></div>
                                ) : (
                                    'Reset Password'
                                )}
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
                    <h3>Set a New Password</h3>
                    <p>Choose a strong password to protect your account</p>
                </div>
            </div>
        </div>
    );
};

export default ResetPasswordPage;