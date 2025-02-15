import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/LoginPage.css';

interface LoginFormData {
    email: string;
    password: string;
}

interface FormErrors {
    email: string;
    password: string;
}

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState<LoginFormData>({
        email: '',
        password: ''
    });
    const [formErrors, setFormErrors] = useState<FormErrors>({
        email: '',
        password: ''
    });
    const [error, setError] = useState<string>('');;
    const [isLoading, setIsLoading] = useState<boolean>(false);

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

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));

        if (name === 'email') validateEmail(value);
        if (name === 'password') validatePassword(value);
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError('');

        const isEmailValid = validateEmail(formData.email);
        const isPasswordValid = validatePassword(formData.password);

        if (!isEmailValid || !isPasswordValid) {
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8081/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Invalid credentials');
            }

            const data = await response.json();
            localStorage.setItem('token', `Bearer ${data.token}`);

            // Check if profile is complete
            const profileResponse = await fetch('http://localhost:8081/api/user/profile-status', {
                headers: {
                    'Authorization': `Bearer ${data.token}`
                }
            })

            const profileData = await profileResponse.json();
            console.log('Profile status response:', profileData);

            // Convert string "true" to boolean
            const isComplete = profileData.message === "true";
            console.log('Is profile complete?:', isComplete);
            if (!isComplete) {
                navigate('/complete-profile');
            } else {
                navigate('/main', {
                    state: {
                        message: 'Login Successful.'
                    }
                });
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="form-container">
                <h1>Job Aggregator Platform</h1>
                <h2>Login</h2>
                <form onSubmit={handleSubmit}>
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
                        />
                        {formErrors.password && (
                            <span className="error-text">{formErrors.password}</span>
                        )}
                    </div>
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}
                    <button
                        type="submit"
                        disabled={isLoading || !formData.email || !formData.password || !!formErrors.email || !!formErrors.password}
                        className={`submit-button ${isLoading || !formData.email || !formData.password ? 'disabled' : ''}`}
                    >
                        {isLoading ? 'Loading...' : 'Login'}
                    </button>
                </form>
                <p>or login up with</p>
                <div className="social-login">
                    <button className="social-btn facebook">Facebook</button>
                    <button className="social-btn google">Google</button>
                    <button className="social-btn apple">Apple</button>
                </div>
                <p>
                    Dont have an account? <a href="/signup">Sign in</a>
                </p>
            </div>
            <div className="image-container" />
        </div>
    );
};

export default LoginPage;