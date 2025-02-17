import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const OAuthCallback: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    useEffect(() => {
        const token: string | null = searchParams.get('token');

        if (token) {
            localStorage.setItem('token', token);
            
            // Redirect to main page
            navigate('/main', {
                state: { 
                    message: 'Login Successful' 
                } as { message: string }
            });
        } else {
            // Handle error
            navigate('/', {
                state: { 
                    error: 'Authentication failed' 
                } as { error: string }
            });
        }

    }, [searchParams, navigate]);

    return (
        <div className="flex justify-center items-center min-h-screen">
            <div className="text-lg">Processing authentication...</div>
        </div>
    );
}

export default OAuthCallback;