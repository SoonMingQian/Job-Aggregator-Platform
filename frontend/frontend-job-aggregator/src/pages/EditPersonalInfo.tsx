import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../styles/EditPage.css';
import Cookies from 'js-cookie';

interface FormData {
    firstName: string;
    lastName: string;
}

const EditPersonalInfo: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [formData, setFormData] = useState<FormData>({
        firstName: location.state?.profile?.firstName || '',
        lastName: location.state?.profile?.lastName || ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = Cookies.get('authToken');
            if (!token) {
                throw new Error('No token found');
            }
            const response = await fetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/profile/personal`, {
                method: 'PUT',
                headers: {
                    'Authorization': token,
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
                    <div className="readonly-field">{location.state?.profile?.email}</div>
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

export default EditPersonalInfo;