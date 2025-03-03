import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import Header from './components/Header';
import ProfilePage from './pages/ProfilePage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import CompleteProfile from './pages/CompleteProfile'
import MainPage from './pages/MainPage'
import SearchResultPage from './pages/SearchResultPage'
import EditPersonalInfo from './pages/EditPersonalInfo';
import EditProfessional from './pages/EditProfessional';
import EditContact from './pages/EditContact';
import EditCV from './pages/EditCV';
import OAuthCallback from './components/OAuthCallback';

const AppContent: React.FC = () => {
  const location = useLocation();
  const showHeader: boolean = !['/login', '/signup'].includes(location.pathname);

  return (
    <>
      {showHeader && <Header />}
      <Routes>
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/complete-profile" element={<CompleteProfile />} />
        <Route path="/" element={<MainPage />} />
        <Route path="/search" element={<SearchResultPage />} />
        <Route path="/edit-profile/personal-info" element={<EditPersonalInfo />} />
        <Route path="/edit-profile/professional" element={<EditProfessional />} />
        <Route path="/edit-profile/contact" element={<EditContact />} />
        <Route path="/edit-profile/cv" element={<EditCV />} />
        <Route path="/oauth/callback" element={<OAuthCallback />} />
      </Routes>
    </>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;