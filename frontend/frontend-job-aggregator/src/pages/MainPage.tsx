import React, { useState, useEffect } from 'react';
import '../styles/MainPage.css';
import Pagination from '../components/Pagination';

interface Job {
    jobId: string;
    title: string;
    company: string;
    location: string;
    jobDescription: string;
    applyLink: string;
    matchScore?: number;
}

const MainPage: React.FC = () => {
    const [searchParams, setSearchParams] = useState({
        title: '',
        location: ''
    });
    const [error, setError] = useState<string>('');
    const [currentPage, setCurrentPage] = useState(1);
    const jobsPerPage = 20;
    const [jobs, setJobs] = useState<Job[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [expandedJob, setExpandedJob] = useState<string | null>(null);

    useEffect(() => {
        const fetchJobs = async () => {
            setIsLoading(true);
            try {
                const response = await fetch('http://localhost:8080/api/redis/jobs/all', {
                    headers: {
                        'Authorization': `${localStorage.getItem('token')}`
                    }
                })
                if (!response.ok) {
                    throw new Error('Failed to fetch jobs');
                }

                const data = await response.json();
                setJobs(data);
            } catch (error) {
                console.error('Error fetching jobs:', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchJobs();
    }, []);

    const getUserAgent = () => {
        return window.navigator.userAgent;
    }

    const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            // Get token and extract userId
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No token found');
            }

            const userAgent = getUserAgent();

            // Get user profile first
            const profileResponse = await fetch('http://localhost:8081/api/user/profile', {
                headers: {
                    'Authorization': token
                }
            });

            const profileData = await profileResponse.json();
            if (!profileResponse.ok) {
                throw new Error('Failed to get user profile');
            }

            const userId = profileData.userId;
            console.log('User ID:', userId);

            console.log('Searching with params:', searchParams); // Debug log
            const response = await fetch(
                `http://127.0.0.1:3002/jobie?title=${encodeURIComponent(searchParams.title)}&job_location=${encodeURIComponent(searchParams.location)}&user_agent=${encodeURIComponent(userAgent)}`,
                {
                    method: 'GET', // Jobs.ie scraping uses GET
                    headers: {
                        'Accept': 'application/json',
                        'User-Agent': userAgent
                    }
                }
            );

            console.log('Response status:', response.status); // Debug log

            const data = await response.json();
            console.log('Response data:', data); // Debug log

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Search failed');
            }

            const matchResponse = await fetch(
                `http://localhost:8082/api/matching/jobs?userId=${userId}&jobTitle=${searchParams.title}&location=${searchParams.location}`,
                {
                    headers: {
                        'Authorization': token
                    }
                }
            );

            // Add error handling for match response
            if (!matchResponse.ok) {
                console.log('Match response status:', matchResponse.status);
                const text = await matchResponse.text(); // Get raw response
                console.log('Match response text:', text);
                // Continue with empty matches if service fails
                setJobs(data.map((job: Job) => ({ ...job, matchScore: 0 })));
                return;
            }

            const matchData = await matchResponse.json();
            console.log('Match data:', matchData);

            // Combine jobs with match scores
            const jobsWithMatches = data.map((job: any) => ({
                ...job,
                matchScore: matchData.find((m: any) => m.jobId === job.jobId)?.score || 0
            }));

            setJobs(jobsWithMatches);
            setCurrentPage(1);
        } catch (error) {
            console.error('Error searching jobs:', error);
            setError(error instanceof Error ? error.message : 'Failed to search jobs');
        } finally {
            setIsLoading(false);
        }
    };

    // Get current jobs
    const indexOfLastJob = currentPage * jobsPerPage;
    const indexOfFirstJob = indexOfLastJob - jobsPerPage;
    const currentJobs = jobs.slice(indexOfFirstJob, indexOfLastJob);

    const toggleJobDescription = (jobId: string) => {
        setExpandedJob(expandedJob === jobId ? null : jobId);
    }

    // Change page
    const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

    return (
        <div className='main-page'>
            <div className='search-section'>
                <h1>Find Your Jobs</h1>
                <form onSubmit={handleSearch} className='search-form'>
                    <input
                        type='text'
                        placeholder='Job Title'
                        value={searchParams.title}
                        onChange={(e) => setSearchParams(prev => ({
                            ...prev,
                            title: e.target.value
                        }))}
                        className='search-input'
                    />
                    <input
                        type='text'
                        placeholder="Location..."
                        value={searchParams.location}
                        onChange={(e) => setSearchParams(prev => ({
                            ...prev,
                            location: e.target.value
                        }))}
                        className="search-input"
                    />
                    <button type="submit" className="search-button" disabled={isLoading}>
                        {isLoading ? 'Searching...' : 'Search'}
                    </button>
                </form>
            </div>
            <div className="jobs-section">
                <table className='jobs-table'>
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Company</th>
                            <th>Location</th>
                            <th>Match Score</th>
                            <th>Action</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {currentJobs.map((job) => (
                            <React.Fragment key={job.jobId}>
                                <tr className='job-row' onClick={() => toggleJobDescription(job.jobId)}>
                                    <td>{job.title}</td>
                                    <td>{job.company}</td>
                                    <td>{job.location}</td>
                                    <td>{job.matchScore}</td>
                                    <td>
                                        <a href={job.applyLink} target="_blank" rel="noopener noreferrer"
                                            className="apply-button">
                                            Apply
                                        </a>
                                    </td>
                                    <td>
                                        <button className="expand-button">
                                            <span className={`expand-icon ${expandedJob === job.jobId ? 'expanded' : ''}`}>
                                                ▶
                                            </span>
                                        </button>
                                    </td>
                                </tr>
                                <tr className={`job-description ${expandedJob === job.jobId ? 'expanded' : ''}`}>
                                    <td colSpan={6}>
                                        {job.jobDescription}
                                    </td>
                                </tr>
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>
                <Pagination
                    currentPage={currentPage}
                    totalPages={Math.ceil(jobs.length / jobsPerPage)}
                    onPageChange={paginate}
                />
            </div>
        </div>
    )
}

export default MainPage;