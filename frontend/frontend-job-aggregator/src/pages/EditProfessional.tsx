import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../styles/EditPage.css';
import Cookies from 'js-cookie';

const EditProfessional: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        jobTitle: location.state?.profile?.profile?.jobTitle || '',
        company: location.state?.profile?.profile?.company || '',
        education: location.state?.profile?.profile?.education || ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const token = Cookies.get('authToken');
            const response = await fetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/profile/professional`, {
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
                <h1>Edit Professional Details</h1>
            </div>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Job Title</label>
                    <input
                        type="text"
                        value={formData.jobTitle}
                        onChange={(e) => setFormData({ ...formData, jobTitle: e.target.value })}
                    />
                </div>
                <div className="form-group">
                    <label>Company</label>
                    <input
                        type="text"
                        value={formData.company}
                        onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    />
                </div>
                <div className="form-group">
                    <label>Education</label>
                    <input
                        type="text"
                        value={formData.education}
                        onChange={(e) => setFormData({ ...formData, education: e.target.value })}
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

export default EditProfessional;