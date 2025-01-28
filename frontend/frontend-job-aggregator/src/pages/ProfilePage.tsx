const ProfilePage = () => {
    const skills = ['JavaScript', 'React', 'Node.js', 'TypeScript', 'Python']
  
    return (
      <div className="profile">
        <div className="profile__card">
          <div className="profile__header">
            <img 
              src="/default-avatar.png" 
              alt="Profile" 
              className="profile__avatar"
            />
            <div className="profile__info">
              <h1>John Doe</h1>
              <p>Full Stack Developer</p>
              <p>Dublin, Ireland</p>
            </div>
          </div>
        </div>
  
        <div className="profile__card">
          <h2>About</h2>
          <p>Passionate developer with 3 years of experience in web development.</p>
        </div>
  
        <div className="profile__card">
          <h2>Skills</h2>
          <div className="profile__skills">
            {skills.map(skill => (
              <span key={skill} className="profile__skill">{skill}</span>
            ))}
          </div>
        </div>
      </div>
    )
  }
  
  export default ProfilePage