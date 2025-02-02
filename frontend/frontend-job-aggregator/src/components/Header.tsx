import React from "react";
import { Link } from "react-router-dom";
import "../styles/Header.css";

const Header: React.FC = (): JSX.Element => {
    return (
        <header className="header">
            <div className="header-container">
                <Link to="/main" className="logo">
                    JobHunt
                </Link>
                <nav className="nav-links">
                    <Link to ="/main">Home</Link>
                    <Link to="/profile">Profile</Link>
                    <button
                        onClick={(): void => {
                            localStorage.removeItem("token");
                            window.location.href = "/";
                        }}
                    >
                        Logout
                    </button>
                </nav>
            </div>
        </header>
    )
}

export default Header;