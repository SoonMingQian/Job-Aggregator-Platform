import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/Header.css";

const Header: React.FC = (): JSX.Element => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const navigate = useNavigate();

    useEffect(() => {
        const checkAuth = () => {
            const token = localStorage.getItem("token");
            setIsAuthenticated(!!token);
        };

        checkAuth();

        // Add event listener for storage changes
        window.addEventListener('storage', checkAuth);
        
        // Custom event listener for auth changes
        window.addEventListener('authChange', checkAuth);

        return () => {
            window.removeEventListener('storage', checkAuth);
            window.removeEventListener('authChange', checkAuth);
        };
    }, []);

    const handleLogout = (): void => {
        localStorage.removeItem("token");
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