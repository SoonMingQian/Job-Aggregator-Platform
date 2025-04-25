import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../styles/EditPage.css';
import Cookies from 'js-cookie';

interface FormData {
    firstName: string;
    lastName: string;
}

const EditPersonalInfo: React.FC = () => {
    const location = useLocation(); // Access the current location state
    const navigate = useNavigate(); // Navigation hook to redirect users
    const [formData, setFormData] = useState<FormData>({
        firstName: location.state?.profile?.firstName || '', // Initialize first name from location state
        lastName: location.state?.profile?.lastName || '' // Initialize last name from location state
    });

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = Cookies.get('authToken'); // Retrieve authentication token from cookies
            if (!token) {
                throw new Error('No token found'); // Handle missing token error
            }
            const response = await fetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/profile/personal`, {
                method: 'PUT',
                headers: {
                    'Authorization': token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData) // Send updated form data
            });

            if (response.ok) {
                navigate('/profile'); 
            }
        } catch (error) {
            console.error('Error updating profile:', error); 
        }
    };

    return (
        <div className="edit-container">
            <div className="edit-header">
                <button className="back-button" onClick={() => navigate('/profile')}>←</button>
                <h1>Edit Personal Information</h1>
            </div>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>First Name</label>
                    <input
                        type="text"
                        value={formData.firstName}
                        onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                    />
                </div>
                <div className="form-group">
                    <label>Last Name</label>
                    <input
                        type="text"
                        value={formData.lastName}
                        onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                    />
                </div>
                <div className="form-group">
                    <label>Email</label>
                    {/* Display email as a read-only field */}
                    <div className="readonly-field">{location.state?.profile?.email}</div>
                </div>
                <div className="button-group">
                    {/* Save changes button */}
                    <button type="submit" className="save-button">Save Changes</button>
                    {/* Cancel button to navigate back to the profile page */}
                    <button type="button" className="cancel-button" onClick={() => navigate('/profile')}>
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
};

export default EditPersonalInfo;