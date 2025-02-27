import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const OAuthCallback: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    useEffect(() => {
        const processAuth = async () => {
            try {
                const token: string | null = searchParams.get('token');

                if (!token) {
                    setErrorMessage('Authentication failed: No token received');
                    setTimeout(() => navigate('/'), 1500);
                    return;
                }

                // Store token
                localStorage.setItem('token', token.startsWith('Bearer ') ? token : `Bearer ${token}`);
                
                // Check if profile is complete
                const response = await fetch('http://localhost:8081/api/user/profile-status', {
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
                    navigate('/complete-profile');
                } else {
                    // Navigate to main page
                    navigate('/main', {
                        state: { 
                            message: 'Login Successful' 
                        }
                    });
                }
            } catch (error) {
                console.error('Error during OAuth callback processing:', error);
                setErrorMessage('Authentication process failed');
                setTimeout(() => navigate('/'), 1500);
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
            ) : null}
        </div>
    );
}

export default OAuthCallback;