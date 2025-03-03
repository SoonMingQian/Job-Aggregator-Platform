import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../styles/EditPage.css';
import Cookies from 'js-cookie';

const EditContact: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        phoneNumber: location.state?.profile?.profile?.phoneNumber || '',
        address: location.state?.profile?.profile?.address || ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = Cookies.get('authToken');
            const response = await fetch('http://localhost:8081/api/user/profile/contact', {
                method: 'PUT',
                headers: {
                    'Authorization': token || '',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
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
                <h1>Edit Contact Information</h1>
            </div>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Phone Number</label>
                    <input
                        type="tel"
                        value={formData.phoneNumber}
                        onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                    />
                </div>
                <div className="form-group">
                    <label>Address</label>
                    <input
                        type="text"
                        value={formData.address}
                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    />
                </div>
                <div className="button-group">
                    <button type="submit" className="save-button">Save Changes</button>
                    <button type="button" className="cancel-button" onClick={() => navigate('/profile')}>
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
};

export default EditContact;