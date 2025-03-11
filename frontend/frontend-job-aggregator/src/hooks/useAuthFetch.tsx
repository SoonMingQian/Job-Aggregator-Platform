import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import { useCallback } from 'react'; // Add this import

// Helper function should be outside the hook
const isTokenExpired = (token: string): boolean => {
    if (!token) return true;

    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(window.atob(base64));
        const currentTime = Math.floor(Date.now() / 1000);
        return payload.exp < currentTime;
    } catch (error) {
        console.error('Error parsing JWT token:', error);
        return true;
    }
};

export const useAuthFetch = () => {
    const navigate = useNavigate();
  
    // Use useCallback to memoize the function
    const authFetch = useCallback(async (url: string, options: RequestInit = {}) => {
        // Get token and verify
        const token = Cookies.get('authToken');
        if (!token || isTokenExpired(token)) {
            console.log("Token expired or not found, redirecting to login");
            Cookies.remove('authToken', { path: '/' });
            navigate('/login');
            throw new Error('Authentication required');
        }

        // Add token to headers
        const headers = {
            ...options.headers,
            'Authorization': token
        };

        // Make the request
        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle unauthorized responses
        if (response.status === 401) {
            console.log("Token rejected by server, redirecting to login");
            Cookies.remove('authToken', { path: '/' });
            navigate('/login');
            throw new Error('Authentication failed');
        }

        return response;
    }, [navigate]); // Only depend on navigate
  
    return { authFetch };
};