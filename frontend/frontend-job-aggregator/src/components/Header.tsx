import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/Header.css";
import Cookies from 'js-cookie';

const Header: React.FC = (): JSX.Element => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const navigate = useNavigate();

    useEffect(() => {
        const checkAuth = () => {
            const token = Cookies.get("authToken");
            setIsAuthenticated(!!token);
        };

        checkAuth();
        
        // Custom event listener for auth changes
        window.addEventListener('authChange', checkAuth);

        const intervalId = setInterval(checkAuth, 60000);

        return () => {
            window.removeEventListener('authChange', checkAuth);
            clearInterval(intervalId);
        };
    }, []);

    const handleLogout = (): void => {
        Cookies.remove("authToken", { path: '/' });
        setIsAuthenticated(false);
        navigate("/");
        // Dispatch auth change event
        window.dispatchEvent(new Event('authChange'));
    };

    return (
        <header className="header">
            <div className="header-container">
                <Link to="/main" className="logo">
                    JobHunt
                </Link>
                <nav className="nav-links">
                    <Link to="/main">Home</Link>
                    {isAuthenticated ? (
                        <>
                            <Link to="/profile">Profile</Link>
                            <button onClick={handleLogout}>Logout</button>
                        </>
                    ) : (
                        <>
                            <Link to="/">Login</Link>
                        </>
                    )}
                </nav>
            </div>
        </header>
    )
}

export default Header;