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
            console.log('Polling for match scores...');
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
                console.log('Received match scores:', matchScores);
                
                setJobs(prevJobs => {
                    const updatedJobs = prevJobs.map(job => ({
                        ...job,
                        matchScore: matchScores[job.jobId] || undefined,
                        isCalculating: !matchScores[job.jobId]
                    }));

                    const allScoresReceived = updatedJobs.every(job => job.matchScore !== undefined);
                    console.log('All scores received:', allScoresReceived);
                    
                    if (allScoresReceived && pollInterval) {
                        console.log('Polling complete - all scores received');
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
            console.log('Starting search for:', { title, location });
            setIsLoading(true);
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No token found');

            console.log('Fetching user profile...');
            const profileResponse = await fetch('http://localhost:8081/api/user/userId', {
                headers: { 'Authorization': token }
            });

            const profileData = await profileResponse.json();
            console.log('User profile received:', profileData);
            if (!profileResponse.ok) throw new Error('Failed to get user profile');

            const userId = profileData.userId;

            // Get browser info from URL params
            const browserInfo = {
                platform: searchParams.get('platform') || navigator.platform,
                language: searchParams.get('language') || navigator.language,
                timezone: searchParams.get('timezone') || Intl.DateTimeFormat().resolvedOptions().timeZone,
                screen_resolution: searchParams.get('screen_resolution') || `${window.screen.width}x${window.screen.height}`,
                color_depth: searchParams.get('color_depth') || window.screen.colorDepth.toString(),
                device_memory: searchParams.get('device_memory') || ((navigator as any).deviceMemory || '8').toString(),
                hardware_concurrency: searchParams.get('hardware_concurrency') || navigator.hardwareConcurrency.toString(),
                user_agent: searchParams.get('user_agent') || navigator.userAgent
            };

            console.log('Making API calls to Jobs.ie and Indeed...');
            const [jobsieResponse, irishjobsResponse] = await Promise.all([
                fetch(
                    `http://127.0.0.1:3002/jobsie?${new URLSearchParams({
                        title: title,
                        job_location: location,
                        userId
                    })}`,
                    {
                        headers: { 'Accept': 'application/json' }
                    }
                ),
                fetch(
                    `http://127.0.0.1:3003/irishjobs?${new URLSearchParams({
                        title: title,
                        job_location: location,
                        userId
                    })}`,
                    {
                        headers: { 'Accept': 'application/json' }
                    }
                ),
                // fetch(
                //     `http://localhost:3001/indeed?${new URLSearchParams({
                //         job_title: title,
                //         job_location: location,
                //         ...browserInfo,
                //         userId
                //     })}`
                // )
            ]);

            console.log('API Response Status:', {
                jobsie: jobsieResponse.status,
                irishjobs: irishjobsResponse.status,
                // indeed: indeedResponse.status
            });

            const [jobsieData, irishjobsData] = await Promise.all([
                jobsieResponse.json(),
                irishjobsResponse.json()
                // indeedResponse.json()
            ]);

            if (!jobsieResponse.ok || !irishjobsResponse.ok) {
                throw new Error('Search failed');
            }

            if (jobsieData.error || irishjobsData.error) {
                throw new Error(jobsieData.error || irishjobsData.error);
            }

            console.log('Jobs received:', {
                jobsie: jobsieData.jobs?.length || 0,
                indeed: irishjobsData.jobs?.length || 0
            });

            // Combine jobs from both sources
            const combinedJobs = [
                ...(jobsieData.jobs || []).map((job: Job) => ({
                    ...job,
                    source: 'jobs.ie',
                    matchScore: undefined,
                    isCalculating: true
                })),
                ...(irishjobsData.jobs || []).map((job: Job) => ({
                    ...job,
                    source: 'irishjobs.ie',
                    matchScore: undefined,
                    isCalculating: true
                })),
                // ...(indeedData.jobs || []).map((job: Job) => {
                //     console.log('Indeed apply link:', {
                //         jobId: job.jobId,
                //         link: job.applyLink
                //     });
                //     return {
                //         ...job,
                //         source: 'indeed',
                //         matchScore: undefined,
                //         isCalculating: true
                //     };
                // })
            ];

            console.log('Total combined jobs:', combinedJobs.length);
            setJobs(combinedJobs);

            // Start polling
            console.log('Starting polling for match scores...');
            if (pollInterval) clearInterval(pollInterval);
            const interval = setInterval(() => pollForScores(userId, token), 2000);
            setPollInterval(interval);

        } catch (error) {
            console.error('Search error:', error);
            setError(error instanceof Error ? error.message : 'Failed to fetch results');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        console.log('SearchResultPage mounted/updated with:', { title, location });
        if (title || location) {
            fetchSearchResults();
        }

        return () => {
            if (pollInterval) {
                console.log('Cleaning up poll interval');
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