import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import '../styles/MainPage.css';
import Pagination from '../components/Pagination';
import SearchBar from '../components/SearchBar';
import DOMPurify from 'dompurify';
import Cookies from 'js-cookie';

interface Job {
    jobId: string;
    title: string;
    company: string;
    location: string;
    jobDescription: string;
    applyLink: string;
    matchScore?: number;
    platform: string;
}

interface BrowserInfo {
    platform: string;
    language: string;
    timezone: string;
    screen_resolution: string;
    color_depth: number;
    device_memory: number;
    hardware_concurrency: number;
    user_agent: string;
}

interface NavigatorUserAgentData {
    platform: string;
    brands: Array<{
        brand: string;
        version: string;
    }>;
    mobile: boolean;
}

interface Navigator {
    userAgentData?: NavigatorUserAgentData;
}

const MainPage: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const [error, setError] = useState<string>('');
    const [currentPage, setCurrentPage] = useState(1);
    const jobsPerPage = 20;
    const [jobs, setJobs] = useState<Job[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [expandedJob, setExpandedJob] = useState<string | null>(null);

    useEffect(() => {
        const initializeJobs = async () => {
            setIsLoading(true);
            try {
                const token = Cookies.get('authToken');
                if (!token) {
                    navigate('/');
                    return;
                }

                const response = await fetch('http://localhost:8080/api/redis/jobs/all', {
                    headers: {
                        'Authorization': token
                    }
                })

                if (!response.ok) {
                    throw new Error('Failed to fetch jobs');
                }

                const data = await response.json();
                setJobs(data);
            } catch (error) {
                console.error('Error initializing jobs:', error);
                setError(error instanceof Error ? error.message : 'Failed to load jobs');
            } finally {
                setIsLoading(false);
            }
        };
        initializeJobs();
    }, []);

    const getBrowserInfo = (): BrowserInfo => {
        return {
            platform: navigator.platform || 'unknown',
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen_resolution: `${window.screen.width}x${window.screen.height}`,
            color_depth: window.screen.colorDepth,
            device_memory: (navigator as any).deviceMemory || 8,
            hardware_concurrency: navigator.hardwareConcurrency || 4,
            user_agent: navigator.userAgent
        };
    };

    const handleSearch = (title: string, location: string) => {
        const browserInfo = getBrowserInfo();
        const searchParams = new URLSearchParams({
            title: title,
            location: location,
            platform: browserInfo.platform,
            language: browserInfo.language,
            timezone: browserInfo.timezone,
            screen_resolution: browserInfo.screen_resolution,
            color_depth: browserInfo.color_depth.toString(),
            device_memory: browserInfo.device_memory.toString(),
            hardware_concurrency: browserInfo.hardware_concurrency.toString(),
            user_agent: browserInfo.user_agent
        });

        navigate(`/search?${searchParams}`);
    };

    // const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    //     const { name, value } = e.target;
    //     setFormData(prev => ({
    //         ...prev,
    //         [name]: value
    //     }));
    // };

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
            <SearchBar
                initialTitle={searchParams.get('title') || ''}
                initialLocation={searchParams.get('location') || ''}
                isLoading={isLoading}
                onSearch={handleSearch}
            />
            <div className="jobs-section">
                <table className='jobs-table'>
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Company</th>
                            <th>Location</th>
                            <th>Platform</th>
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
                                    <td>{job.platform}</td>
                                    <td>
                                        <a
                                            href={job.applyLink}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="apply-button"
                                            onClick={(e) => e.stopPropagation()}
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
                                    <td colSpan={6}>
                                        <div
                                            className="job-description-content"
                                            dangerouslySetInnerHTML={{
                                                __html: DOMPurify.sanitize(job.jobDescription)
                                            }}
                                        />
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