import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Cookies from 'js-cookie';

const OAuthCallback: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null); 

    useEffect(() => {
        const processAuth = async () => {
            try {
                const token: string | null = searchParams.get('token');
                const registration = searchParams.get('registration'); 
                const action = searchParams.get('action'); 
                if (!token) {
                    setErrorMessage('Authentication failed: No token received');
                    setTimeout(() => navigate('/login'), 1500);
                    return;
                }

                // Set appropriate message based on registration status and action
                if (action === 'signup' && registration === 'new') {
                    setSuccessMessage('Account created successfully!');
                } else if (action === 'signup' && registration === 'existing') {
                    setSuccessMessage('Welcome back! You already had an account.');
                } else {
                    setSuccessMessage('Successfully logged in!');
                }

                // Store token in cookie instead of localStorage
                const formattedToken = token.startsWith('Bearer ') ? token : `Bearer ${token}`;

                // Set the cookie with secure options
                Cookies.set('authToken', formattedToken, {
                    expires: 31, // expires in 7 days
                    secure: window.location.protocol === 'https:', // only send over HTTPS
                    sameSite: 'strict', // restrict to same site
                    path: '/' // available across the site
                });

                // Check if profile is complete
                const response = await fetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/profile-status`, {
                    headers: {
                        'Authorization': token.startsWith('Bearer ') ? token : `Bearer ${token}`
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Failed to check profile status');
                }
                
                const data = await response.json();
                const isComplete = data.message === "true";
                
                if (!isComplete) {
                    // Navigate to profile completion page
                    setTimeout(() => {
                        navigate('/complete-profile', {
                            state: { 
                                message: successMessage || 'Authentication successful'
                            }
                        });
                    }, 1500);
                } else {
                    // Navigate to main page
                    setTimeout(() => {
                        navigate('/', {
                            state: { 
                                message: successMessage || 'Authentication successful'
                            }
                        });
                    }, 1500);
                }
            } catch (error) {
                console.error('Error during OAuth callback processing:', error);
                setErrorMessage('Authentication process failed');
                setTimeout(() => navigate('/login'), 1500);
            } finally {
                setIsLoading(false);
            }
        };

        processAuth();
    }, [searchParams, navigate]);

    return (
        <div className="flex justify-center items-center min-h-screen flex-col">
            {isLoading ? (
                <div className="text-lg">Processing authentication...</div>
            ) : errorMessage ? (
                <div className="text-lg text-red-500">{errorMessage}</div>
            ) : successMessage ? (
                <div className="text-lg text-green-500">{successMessage}</div>
            ) : null}
        </div>
    );
}

export default OAuthCallback;