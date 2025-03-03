import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/CompleteProfile.css";
import Cookies from 'js-cookie';

interface UserInfoFormData {
    phoneNumber: string;
    address: string;
    education: string;
    jobTitle: string;
    company: string;
    cv: File | null;
}

interface FormErrors {
    phoneNumber: string;
    address: string;
    education: string;
    jobTitle: string;
    company: any;
    cv: string;
}

const CompleteProfile: React.FC = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState<UserInfoFormData>({
        phoneNumber: "",
        address: "",
        education: "",
        jobTitle: "",
        company: "",
        cv: null,
    });

    const [formErrors, setFormErrors] = useState<FormErrors>({
        phoneNumber: '',
        address: '',
        education: '',
        jobTitle: '',
        company: '',
        cv: ''
    });

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>('');

    const validatePhoneNumber = (phoneNumber: string): boolean => {
        if (!phoneNumber) {
            setFormErrors(prev => ({ ...prev, phoneNumber: 'Phone number is required' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, phoneNumber: '' }));
        return true;
    }

    const validateAddress = (address: string): boolean => {
        if (!address) {
            setFormErrors(prev => ({ ...prev, address: 'Address is required' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, address: '' }));
        return true;
    }

    const validateCV = (file: File | null): boolean => {
        if (!file) {
            setFormErrors(prev => ({ ...prev, cv: 'CV is required' }));
            return false;
        }
        const validTypes = ['application/pdf'];
        if (!validTypes.includes(file.type)) {
            setFormErrors(prev => ({ ...prev, cv: 'Please upload PDF or DOC/DOCX file' }));
            return false;
        }
        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            setFormErrors(prev => ({ ...prev, cv: 'File size should be less than 5MB' }));
            return false;
        }
        setFormErrors(prev => ({ ...prev, cv: '' }));
        return true;
    }
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFormData(prev => ({
                ...prev,
                cv: e.target.files![0]
            }));
        }
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const isValid =
            validatePhoneNumber(formData.phoneNumber) &&
            validateAddress(formData.address) &&
            validateCV(formData.cv);

        if (!isValid) {
            return;
        }
        setIsLoading(true);
        setError('');

        try {
            const token = Cookies.get('authToken');
            if (!token) {
                throw new Error('Token not found');
            }
            // Remove Bearer if present
            const actualToken = token.startsWith('Bearer ') ? token.substring(7) : token;

            const formDataToSend = new FormData();
            formDataToSend.append('phoneNumber', formData.phoneNumber);
            formDataToSend.append('address', formData.address);
            formDataToSend.append('education', formData.education);
            formDataToSend.append('jobTitle', formData.jobTitle);
            formDataToSend.append('company', formData.company);
            if (formData.cv) {
                formDataToSend.append('cv', formData.cv);
            }

            console.log('Form data being sent:', Object.fromEntries(formDataToSend));

            const response = await fetch('http://localhost:8081/api/user/complete-profile', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${actualToken}`
                },
                body: formDataToSend
            });

            // Get detailed error message from backend
            const responseData = await response.json();
            if (!response.ok) {
                console.error('Profile completion error:', responseData);
                throw new Error(responseData.message || 'Error completing profile');
            }

            // Use userId from backend response
            const userId = responseData.userId;
            console.log('UserId from backend:', userId);

            // Create form data with userId
            const formDataToAnalysis = new FormData();
            formDataToAnalysis.append('userId', userId);
            if (formData.cv) {
                formDataToAnalysis.append('file', formData.cv);
            }
            console.log('userId:', userId);
            // Send to text extraction service
            const analysisResponse = await fetch('http://127.0.0.1:5000/extract-text', {
                method: 'POST',
                body: formDataToAnalysis
            })

            if (!analysisResponse.ok) {
                const analysisError = await analysisResponse.json();
                console.error('Text extraction error:', analysisError);
                throw new Error(analysisError.message || 'Error processing CV');
            }

            navigate('/', {
                state: { message: 'Profile completed successfully.' }
            });
        } catch (err) {
            console.error('Full error:', err);
            setError(err instanceof Error ? err.message : 'Failed to complete profile');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="complete-profile-page">
            <div className="form-container">
                <h1>Complete Your Profile</h1>
                <h2>Just a few more details...</h2>
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label htmlFor="phoneNumber">Phone Number</label>
                        <input
                            type="tel"
                            id="phoneNumber"
                            name="phoneNumber"
                            value={formData.phoneNumber}
                            onChange={handleInputChange}
                            required
                        />
                        {formErrors.phoneNumber && (
                            <span className="error-text">{formErrors.phoneNumber}</span>
                        )}
                    </div>
                    <div className="input-group">
                        <label htmlFor="address">Address</label>
                        <textarea
                            id="address"
                            name="address"
                            value={formData.address}
                            onChange={handleInputChange}
                            required
                        />
                        {formErrors.address && (
                            <span className="error-text">{formErrors.address}</span>
                        )}
                    </div>
                    <div className="input-group">
                        <label htmlFor="education">Education</label>
                        <textarea
                            id="education"
                            name="education"
                            value={formData.education}
                            onChange={handleInputChange}
                            required
                        />
                        {formErrors.education && (
                            <span className="error-text">{formErrors.education}</span>
                        )}
                    </div>
                    <h3>Most Recent Work Experience</h3>
                    <div className="input-group">
                        <label htmlFor="jobTitle">Job Title</label>
                        <textarea
                            id="jobTitle"
                            name="jobTitle"
                            value={formData.jobTitle}
                            onChange={handleInputChange}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label htmlFor="company">Company</label>
                        <input
                            type="text"
                            id="company"
                            name="company"
                            value={formData.company}
                            onChange={handleInputChange}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label htmlFor="cv">Upload CV (PDF Only)</label>
                        <input
                            type="file"
                            id="cv"
                            name="cv"
                            accept=".pdf"
                            onChange={handleFileChange}
                            required
                        />
                        {formErrors.cv && (
                            <span className="error-text">{formErrors.cv}</span>
                        )}
                    </div>
                    {error && <div className="error-message">{error}</div>}
                    <button
                        type="submit"
                        disabled={isLoading}
                        className={`submit-button ${isLoading ? 'disabled' : ''}`}
                    >
                        {isLoading ? 'Completing...' : 'Complete Profile'}
                    </button>
                </form>
            </div>
        </div>
    )
}

export default CompleteProfile;