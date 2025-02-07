import React, { useState, useEffect } from 'react';
import '../styles/ProfilePage.css';
import { useNavigate } from 'react-router-dom';

interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  profile: {
    phoneNumber: string;
    address: string;
    education: string;
    jobTitle: string;
    company: string;
    cvName?: string;
  };
}

const ProfilePage: React.FC = (): JSX.Element => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleEditPersonalInfo = () => {
    navigate('/edit-profile/personal-info', { state: { profile } });
  };

  const handleEditProfessional = () => {
    navigate('/edit-profile/professional', { state: { profile } });
  };

  const handleEditContact = () => {
    navigate('/edit-profile/contact', { state: { profile } });
  };

  const handleEditCV = () => {
    navigate('/edit-profile/cv', { state: { profile } });
  };

  useEffect(() => {
    const fetchProfile = async (): Promise<void> => {
      try {
        const token = localStorage.getItem('token');
        if (!token) throw new Error('No token found');

        const profileResponse = await fetch('http://localhost:8081/api/user/profile', {
          headers: { 'Authorization': token }
        });

        if (!profileResponse.ok) {
          throw new Error('Failed to fetch profile');
        }

        const data: UserProfile = await profileResponse.json();
        setProfile(data);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  if (isLoading) {
    return <div className="loading-container">Loading...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (!profile) {
    return <div className="no-profile">No profile data found</div>;
  }

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h1>Profile</h1>
      </div>
      <div className="profile-content">
        <div className="profile-section" onClick={handleEditPersonalInfo}>
          <div className="section-header">
            <h2>Personal Information</h2>
          </div>
          <p>Name: {profile.firstName} {profile.lastName}</p>
          <p>Email: {profile.email}</p>
          <button className="edit-button"></button>
        </div>

        <div className="profile-section" onClick={handleEditProfessional}>
          <div className="section-header">
            <h2>Professional Details</h2>
          </div>
          <p>Job Title: {profile.profile.jobTitle}</p>
          <p>Company: {profile.profile.company}</p>
          <p>Education: {profile.profile.education}</p>
          <button className="edit-button"></button>
        </div>

        <div className="profile-section" onClick={handleEditContact}>
          <div className="section-header">
            <h2>Contact Information</h2>
          </div>
          <p>Phone: {profile.profile.phoneNumber}</p>
          <p>Address: {profile.profile.address}</p>
          <button className="edit-button"></button>
        </div>

        {profile.profile.cvName && (
          <div className="profile-section" onClick={handleEditCV}>
            <div className="section-header">
              <h2>CV</h2>
            </div>
            <p>{profile.profile.cvName}</p>
            <button className="edit-button"></button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProfilePage