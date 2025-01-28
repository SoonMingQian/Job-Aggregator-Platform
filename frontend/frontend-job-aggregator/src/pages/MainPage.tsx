import React, { useState, useEffect } from 'react';
import '../styles/MainPage.css';

interface Job {
    jobId: string;
    title: string;
    company: string;
    location: string;
    jobDescription: string;
    applyLink: string;
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

    const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            console.log('Searching with params:', searchParams); // Debug log
            const response = await fetch(
                `http://127.0.0.1:3002/jobie?title=${encodeURIComponent(searchParams.title)}&job_location=${encodeURIComponent(searchParams.location)}`,
                {
                    method: 'GET', // Jobs.ie scraping uses GET
                    headers: {
                        'Accept': 'application/json'
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

            if (Array.isArray(data)) {
                setJobs(data);
                setCurrentPage(1); // Reset to first page
            } else {
                throw new Error('Invalid response format');
            }
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
                <h1>Find Jobs</h1>
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
                                    <td colSpan={5}>
                                        {job.jobDescription}
                                    </td>
                                </tr>
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>
                <div className='pagination'>
                    {Array.from({ length: Math.ceil(jobs.length / jobsPerPage) }).map((_, index) => (
                        <button
                            key={index}
                            onClick={() => paginate(index + 1)}
                            className={`page-button ${currentPage === index + 1 ? 'active' : ''}`}
                        >
                            {index + 1}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default MainPage;