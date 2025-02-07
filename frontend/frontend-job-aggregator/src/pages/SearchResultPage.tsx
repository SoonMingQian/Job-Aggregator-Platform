import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
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
    isCalculating?: boolean;
}

interface SearchResponse {
    jobs: Job[];
    error?: string;
}

const SearchResultPage: React.FC = (): JSX.Element => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    const [jobs, setJobs] = useState<Job[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>('');
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [expandedJob, setExpandedJob] = useState<string | null>(null);
    const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

    const jobsPerPage: number = 20;
    const title: string = searchParams.get('title') || '';
    const location: string = searchParams.get('location') || '';

    const pollForScores = async (userId: string, token: string) => {
        try {
            const matchResponse = await fetch(
                `http://localhost:8082/api/redis/match/${userId}`,
                {
                    headers: {
                        'Authorization': token
                    }
                }
            );

            if (matchResponse.ok) {
                const matchScores = await matchResponse.json();
                setJobs(prevJobs => {
                    const updatedJobs = prevJobs.map(job => ({
                        ...job,
                        matchScore: matchScores[job.jobId] || undefined,
                        isCalculating: !matchScores[job.jobId]
                    }));

                    const allScoresReceived = updatedJobs.every(job => job.matchScore !== undefined);
                    if (allScoresReceived && pollInterval) {
                        clearInterval(pollInterval);
                        setPollInterval(null);
                    }

                    return updatedJobs;
                });
            }
        } catch (error) {
            console.error('Error polling scores:', error);
        }
    };

    const fetchSearchResults = async (): Promise<void> => {
        try {
            setIsLoading(true);
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No token found');

            const profileResponse = await fetch('http://localhost:8081/api/user/userId', {
                headers: { 'Authorization': token }
            });

            const profileData = await profileResponse.json();
            if (!profileResponse.ok) throw new Error('Failed to get user profile');

            const userId = profileData.userId;

            const jobsieResponse = await fetch(
                `http://127.0.0.1:3002/jobie?title=${encodeURIComponent(title)}&job_location=${encodeURIComponent(location)}&userId=${userId}`,
                {
                    headers: { 'Accept': 'application/json' }
                }
            );

            if (!jobsieResponse.ok) throw new Error('Search failed');

            const data: SearchResponse = await jobsieResponse.json();

            // Set initial jobs
            const initialJobs = data.jobs.map(job => ({
                ...job,
                matchScore: undefined,
                isCalculating: true
            }));
            setJobs(initialJobs);

            // Start polling
            if (pollInterval) clearInterval(pollInterval);
            const interval = setInterval(() => pollForScores(userId, token), 2000);
            setPollInterval(interval);

        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to fetch results');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (title || location) {
            fetchSearchResults();
        }

        return () => {
            if (pollInterval) {
                clearInterval(pollInterval);
                setPollInterval(null);
            }
        };
    }, [title, location]);

    const toggleJobDescription = (jobId: string): void => {
        setExpandedJob(prevId => prevId === jobId ? null : jobId);
    }

    const handleBackClick = (): void => {
        navigate('/main');
    };

    const currentJobs: Job[] = jobs.slice(
        (currentPage - 1) * jobsPerPage,
        currentPage * jobsPerPage
    );

    return (
        <div className="main-page">
            <div className='search-results-header'>
                <button onClick={handleBackClick} className="back-button">
                    Back to Search
                </button>
            </div>

            {isLoading ? (
                <div className="loading-container">
                    <div className="loader"></div>
                </div>
            ) : error ? (
                <div className="error-message">{error}</div>
            ) : (
                <div className='jobs-section'>
                    <span>Search Results for "{title}" in {location}</span>
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
                            {currentJobs.map((job: Job) => (
                                <React.Fragment key={job.jobId}>
                                    <tr className='job-row' onClick={() => toggleJobDescription(job.jobId)}>
                                        <td>{job.title}</td>
                                        <td>{job.company}</td>
                                        <td>{job.location}</td>
                                        <td>
                                            {job.matchScore === undefined ? (
                                                <span className="calculating">Calculating...</span>
                                            ) : (
                                                `${job.matchScore}%`
                                            )}
                                        </td>
                                        <td>
                                            <a
                                                href={job.applyLink}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="apply-button"
                                                onClick={(e: React.MouseEvent) => e.stopPropagation()}
                                            >
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
                                        <td colSpan={6}>{job.jobDescription}</td>
                                    </tr>
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>

                    {jobs.length > 0 && (
                        <Pagination
                            currentPage={currentPage}
                            totalPages={Math.ceil(jobs.length / jobsPerPage)}
                            onPageChange={setCurrentPage}
                        />
                    )}
                </div>
            )}
        </div>
    )
}

export default SearchResultPage;