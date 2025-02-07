import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/EditPage.css';

const EditCV: React.FC = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        try {
            setIsLoading(true);
            setError(null);
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No token found');

            // Upload CV first and get userId from response
            const formData = new FormData();
            formData.append('cv', file);

            const cvResponse = await fetch('http://localhost:8081/api/user/profile/cv', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token.replace('Bearer ', '')}`
                },
                body: formData
            });

            if (!cvResponse.ok) {
                const errorData = await cvResponse.json();
                throw new Error(errorData.message || 'Failed to upload CV');
            }

            const responseData = await cvResponse.json();
            const userId = responseData.userId;

            // Send to analysis with userId from response
            const formDataAnalysis = new FormData();
            formDataAnalysis.append('userId', userId);
            formDataAnalysis.append('file', file);

            const analysisResponse = await fetch('http://127.0.0.1:5000/extract-text', {
                method: 'POST',
                body: formDataAnalysis
            });

            if (!analysisResponse.ok) {
                throw new Error('Failed to analyze CV');
            }

            navigate('/profile');
        } catch (error) {
            console.error('Error:', error);
            setError(error instanceof Error ? error.message : 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="edit-container">
            <div className="edit-header">
                <button className="back-button" onClick={() => navigate('/profile')}>←</button>
                <h1>Upload CV</h1>
            </div>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Select CV File</label>
                    <input
                        type="file"
                        accept=".pdf,.doc,.docx"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                    />
                </div>
                <div className="button-group">
                    <button type="submit" className="save-button" disabled={!file}>
                        Upload CV
                    </button>
                    <button type="button" className="cancel-button" onClick={() => navigate('/profile')}>
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
};

export default EditCV;