import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/SignupPage.css';

interface SignupFormData {
    firstName: string;
    lastName: string;
    email: string;
    password: string;
    confirmPassword: string;
}

interface SignupFormErrors {
    firstName: string;
    lastName: string;
    email: string;
    password: string;
    confirmPassword: string;
}

const SignupPage: React.FC = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState<SignupFormData>({
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [formErrors, setFormErrors] = useState<SignupFormErrors>({
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [error, setError] = useState<string>('');;
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const validateFirstName = (firstName: string) => {
        const regex = /^[a-zA-Z\s]+$/;
        if (!firstName) {
            setFormErrors(prev => ({ ...prev, firstName: 'First name is required' }));
            return false;
        }
        if (!regex.test(firstName)) {
            setFormErrors(prev => ({ ...prev, firstName: 'First name must contain only letters' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, firstName: '' }));
        return true;
    }

    const validateLastName = (firstName: string) => {
        const regex = /^[a-zA-Z\s]+$/;
        if (!firstName) {
            setFormErrors(prev => ({ ...prev, firstName: 'Last name is required' }));
            return false;
        }
        if (!regex.test(firstName)) {
            setFormErrors(prev => ({ ...prev, firstName: 'Last name must contain only letters' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, firstName: '' }));
        return true;
    }

    const validateEmail = (email: string) => {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) {
            setFormErrors(prev => ({ ...prev, email: 'Email is required' }));
            return false;
        }
        if (!regex.test(email)) {
            setFormErrors(prev => ({ ...prev, email: 'Invalid email format' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, email: '' }));
        return true;
    }

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

    const validateConfirmPassword = (confirmPassword: string) => {
        if (confirmPassword !== formData.password) {
            setFormErrors(prev => ({ ...prev, confirmPassword: 'Passwords do not match' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, confirmPassword: '' }));
        return true;
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));

        // Validate on input change
        switch (name) {
            case 'firstName':
                validateFirstName(value);
                break;
            case 'lastName':
                validateLastName(value);
                break;
            case 'email':
                validateEmail(value);
                break;
            case 'password':
                validatePassword(value);
                break;
            case 'confirmPassword':
                validateConfirmPassword(value);
                break;
        }
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError('');

        const isValid =
            validateFirstName(formData.firstName) &&
            validateLastName(formData.lastName) &&
            validateEmail(formData.email) &&
            validatePassword(formData.password) &&
            validateConfirmPassword(formData.confirmPassword);

        if (!isValid) return;

        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8081/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Registration failed');
            }

            navigate('/', {
                state: {
                    message: 'Registration successful! Please login.'
                }
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Register failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="signup-page">
            <div className="form-container">
                <h1>Job Aggregator Platform</h1>
                <h2>Signup</h2>
                <form onSubmit={handleSubmit}>
                    <div className="name-row">
                        <div className="input-group half">
                            <label htmlFor="firstName">First Name</label>
                            <input
                                type="text"
                                id="firstName"
                                name="firstName"
                                placeholder="John"
                                value={formData.firstName}
                                onChange={handleInputChange}
                                required
                                className={formErrors.firstName ? 'error' : ''}
                            />
                            {formErrors.firstName && (
                                <span className="error-text">{formErrors.firstName}</span>
                            )}
                        </div>
                        <div className="input-group half">
                            <label htmlFor="lastName">Last Name</label>
                            <input
                                type="text"
                                id="lastName"
                                name="lastName"
                                placeholder="Doe"
                                value={formData.lastName}
                                onChange={handleInputChange}
                                required
                                className={formErrors.lastName ? 'error' : ''}
                            />
                            {formErrors.lastName && (
                                <span className="error-text">{formErrors.lastName}</span>
                            )}
                        </div>
                    </div>
                    <div className="input-group">
                        <label htmlFor="email">E-mail</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            placeholder="example@email.com"
                            value={formData.email}
                            onChange={handleInputChange}
                            required
                            className={formErrors.email ? 'error' : ''}
                        />
                        {formErrors.email && (
                            <span className="error-text">{formErrors.email}</span>
                        )}
                    </div>
                    <div className="input-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            placeholder="••••••••"
                            value={formData.password}
                            onChange={handleInputChange}
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
                            placeholder="••••••••"
                            value={formData.confirmPassword}
                            onChange={handleInputChange}
                            required
                            className={formErrors.confirmPassword ? 'error' : ''}
                        />
                        {formErrors.confirmPassword && (
                            <span className="error-text">{formErrors.confirmPassword}</span>
                        )}
                    </div>
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}
                    <button
                        type="submit"
                        disabled={isLoading || !formData.firstName || !formData.lastName || 
                                !formData.email || !formData.password || !formData.confirmPassword ||
                                !!formErrors.firstName || !!formErrors.lastName || !!formErrors.email || 
                                !!formErrors.password || !!formErrors.confirmPassword}
                    >
                        {isLoading ? 'Creating Account...' : 'Sign Up'}
                    </button>
                </form>
                <p>or signup with</p>
                <div className="social-login">
                    <button className="social-btn facebook">Facebook</button>
                    <button className="social-btn google">Google</button>
                    <button className="social-btn apple">Apple</button>
                </div>
            </div>
            <div className="image-container">
                <div className="signup-section">
                    <h3>Already have an account?</h3>
                    <p>Login to continue your journey</p>
                    <button onClick={() => navigate('/')} className="signup-button">
                        Login
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SignupPage;