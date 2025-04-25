import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../styles/EditPage.css';
import Cookies from 'js-cookie';

const EditContact: React.FC = () => {
    const location = useLocation(); // Access the current location state
    const navigate = useNavigate(); // Navigation hook to redirect users
    const [formData, setFormData] = useState({
        phoneNumber: location.state?.profile?.profile?.phoneNumber || '', // Initialize phone number
        address: location.state?.profile?.profile?.address || '' // Initialize address
    });

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = Cookies.get('authToken'); // Retrieve auth token from cookies
            const response = await fetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/profile/contact`, {
                method: 'PUT',
                headers: {
                    'Authorization': token || '', // Add authorization header
                    'Content-Type': 'application/json' // Specify content type
                },
                body: JSON.stringify(formData) // Send updated contact info
            });

            if (response.ok) {
                navigate('/profile'); // Redirect to profile page on success
            }
        } catch (error) {
            console.error('Error updating profile:', error); // Log any errors
        }
    };

    return (
        <div className="edit-container">
            <div className="edit-header">
                {/* Back button to navigate to the profile page */}
                <button className="back-button" onClick={() => navigate('/profile')}>←</button>
                <h1>Edit Contact Information</h1>
            </div>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Phone Number</label>
                    {/* Input field for phone number */}
                    <input
                        type="tel"
                        value={formData.phoneNumber}
                        onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                    />
                </div>
                <div className="form-group">
                    <label>Address</label>
                    {/* Input field for address */}
                    <input
                        type="text"
                        value={formData.address}
                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    />
                </div>
                <div className="button-group">
                    {/* Save changes button */}
                    <button type="submit" className="save-button">Save Changes</button>
                    {/* Cancel button to navigate back to profile */}
                    <button type="button" className="cancel-button" onClick={() => navigate('/profile')}>
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
};

export default EditContact;