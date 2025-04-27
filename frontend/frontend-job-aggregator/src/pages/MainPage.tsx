import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom'; // Add useLocation
import '../styles/MainPage.css';
import Pagination from '../components/Pagination';
import SearchBar from '../components/SearchBar';
import DOMPurify from 'dompurify';
import Cookies from 'js-cookie';
import { useAuthFetch } from '../hooks/useAuthFetch';
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

interface SearchHistoryItem {
    id: string;
    title: string;
    location: string;
    timestamp: string;
}

const MainPage: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const location = useLocation(); // Add this line
    const { authFetch } = useAuthFetch();
    const [error, setError] = useState<string>('');
    const [currentPage, setCurrentPage] = useState(1);
    const jobsPerPage = 20;
    const [jobs, setJobs] = useState<Job[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [expandedJob, setExpandedJob] = useState<string | null>(null);
    const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
    const [showSearchHistory, setShowSearchHistory] = useState(false)
    const searchContainerRef = useRef<HTMLDivElement>(null)
    const initializeRef = useRef(false);
    const [sortField, setSortField] = useState<keyof Job | null>(null);
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

    useEffect(() => {
        // Check if we just completed a Google OAuth login
        const justLoggedIn = 
            location.search.includes('login=success') || 
            location.search.includes('code=') ||  // Google auth returns a code
            location.state?.loginSuccess || 
            location.state?.message?.includes('successful');
        
        // If we have an auth token after OAuth, dispatch auth change
        if (justLoggedIn && Cookies.get('authToken')) {
            console.log('OAuth login detected, updating authentication state');
            window.dispatchEvent(new Event('authChange'));
        }
    }, [location]);
    
    const handleSort = (field: keyof Job) => {
        // If clicking the same field, toggle direction
        if (field === sortField) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            // Default to descending for match scores, ascending for everything else
            setSortField(field);
            setSortDirection(field === 'matchScore' ? 'desc' : 'asc');
        }
    };
    
    useEffect(() => {
        // Only run initialization once
        if (!initializeRef.current) {
            const initialize = async () => {
                // Load search history first and wait for it to complete
                const historyString = Cookies.get('searchHistory');
                console.log("Retrieved search history from cookies:", historyString);

                let recentSearch = null;
                if (!historyString) {
                    setSearchHistory([]);
                } else {
                    try {
                        const history = JSON.parse(historyString);
                        console.log("Parsed history:", history);

                        if (Array.isArray(history) && history.length > 0) {
                            // Sort by timestamp (newest first) to ensure we get the most recent
                            const sortedHistory = [...history].sort((a, b) =>
                                new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
                            );


                            // Add check to prevent unnecessary updates
                            if (JSON.stringify(sortedHistory) !== JSON.stringify(searchHistory)) {
                                setSearchHistory(sortedHistory);
                            }

                            // But we can use the local variable right away
                            recentSearch = sortedHistory[0];
                        }
                    } catch (e) {
                        console.error('Error parsing search history from cookie:', e);
                    }
                }
                // Now initialize jobs with the search history data we have
                setIsLoading(true);
                try {
                    const token = Cookies.get('authToken');
                    if (!token) {
                        navigate('/login');
                        return;
                    }

                    // Use the search history we just loaded
                    const searchTitle = recentSearch?.title || "";
                    const searchLocation = recentSearch?.location || "";

                    console.log(`Using recent search: title=${searchTitle}, location=${searchLocation}`);

                    // Build the URL with query parameters
                    const url = `${import.meta.env.VITE_API_JOBS_SERVICE}/api/jobs/relevant?title=${encodeURIComponent(searchTitle)}&location=${encodeURIComponent(searchLocation)}`;

                    const response = await authFetch(url);

                    if (!response.ok) {
                        throw new Error('Failed to fetch jobs');
                    }

                    const data = await response.json();
                    setJobs(data);
                } catch (error) {
                    console.error('Error initializing jobs:', error);
                    if (!(error instanceof Error &&
                        (error.message === 'Authentication required' ||
                            error.message === 'Authentication failed'))) {
                        setError(error instanceof Error ? error.message : 'Failed to load jobs');
                    }
                } finally {
                    setIsLoading(false);
                }
            };

            initialize();
            initializeRef.current = true; // Mark as initialized
        }

        const handleClickOutside = (event: MouseEvent) => {
            if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
                setShowSearchHistory(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        }

    }, [navigate]);

    const saveSearchHistory = (title: string, location: string) => {
        if (!title && !location) return;

        const id = Date.now().toString();
        const timestamp = new Date().toISOString();

        const newHistoryItem: SearchHistoryItem = {
            id,
            title,
            location,
            timestamp
        };

        const updatedHistory = [
            newHistoryItem,
            ...searchHistory.filter(item =>
                !(item.title === title && item.location === location)
            ).slice(0, 5)
        ];

        setSearchHistory(updatedHistory);

        try {
            Cookies.set('searchHistory', JSON.stringify(updatedHistory), {
                expires: 30,
                sameSite: 'strict',
                secure: window.location.protocol === 'https:',
                path: '/'
            });
            // After trying to save the cookie
            console.log("After saving, cookie value:", Cookies.get('searchHistory'));
        } catch (e) {
            console.error('Error saving search history to cookie:', e);

            if (updatedHistory.length > 4) {
                const shorterHistory = updatedHistory.slice(0, 3);
                try {
                    Cookies.set('searchHistory', JSON.stringify(shorterHistory), {
                        expires: 30,
                        sameSite: 'strict',
                        secure: window.location.protocol === 'https:',
                        path: '/'
                    });
                } catch (e) {
                    console.error('Failed to save even shorter history:', e);
                }
            }
        }
    };


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
        // First, save this search to history
        saveSearchHistory(title, location);

        // Hide search history after selecting
        setShowSearchHistory(false);

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

    const clearSearchHistory = () => {
        setSearchHistory([]);
        Cookies.remove('searchHistory', { path: '/' });
    };

    // Sort jobs based on current sort settings
    const sortedJobs = React.useMemo(() => {
        if (!sortField) return jobs;
        
        return [...jobs].sort((a, b) => {
            // Handle matchScore specially since it might be undefined
            if (sortField === 'matchScore') {
                const scoreA = a[sortField] || 0;
                const scoreB = b[sortField] || 0;
                return sortDirection === 'asc' ? scoreA - scoreB : scoreB - scoreA;
            }
            
            // Handle string comparisons
            const valueA = String(a[sortField] || '').toLowerCase();
            const valueB = String(b[sortField] || '').toLowerCase();
            
            if (valueA < valueB) return sortDirection === 'asc' ? -1 : 1;
            if (valueA > valueB) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }, [jobs, sortField, sortDirection]);

    // Get current jobs from the sorted list
    const indexOfLastJob = currentPage * jobsPerPage;
    const indexOfFirstJob = indexOfLastJob - jobsPerPage;
    const currentJobs = sortedJobs.slice(indexOfFirstJob, indexOfLastJob);

    const toggleJobDescription = (jobId: string) => {
        setExpandedJob(expandedJob === jobId ? null : jobId);
    }

    // Change page
    const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

    return (
        <div className='main-page'>
            <div className='search-container' ref={searchContainerRef}>
                <SearchBar
                    initialTitle={searchParams.get('title') || ''}
                    initialLocation={searchParams.get('location') || ''}
                    isLoading={isLoading}
                    onSearch={handleSearch}
                    onFocus={() => setShowSearchHistory(true)}
                />

                {/* Add error message display */}
                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}

                {showSearchHistory && searchHistory.length > 0 && (
                    <div className="search-history">
                        <div className="search-history-header">
                            <h3>Recent Searches</h3>
                            <button
                                className="clear-history-button"
                                onClick={clearSearchHistory}
                            >
                                Clear All
                            </button>
                        </div>
                        <ul className="search-history-list">
                            {searchHistory.map((item) => (
                                <li key={item.id} className="search-history-item">
                                    <button
                                        onClick={() => handleSearch(item.title, item.location)}
                                        className="search-history-button"
                                    >
                                        <div className="search-history-terms">
                                            <span className="search-term">{item.title}</span>
                                            {item.location && (
                                                <>
                                                    <span className="search-separator">in</span>
                                                    <span className="search-term">{item.location}</span>
                                                </>
                                            )}
                                        </div>
                                        <span className="search-history-time">
                                            {new Date(item.timestamp).toLocaleDateString()}
                                        </span>
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            <div className="recommended-section">
                <div className="section-header">
                    <h2>Recommended Jobs For You</h2>
                </div>
            </div>

            <div className="jobs-section">
                <table className='jobs-table'>
                    <thead>
                        <tr>
                            <th 
                                onClick={() => handleSort('title')}
                                className={sortField === 'title' ? `sorted-${sortDirection}` : ''}
                            >
                                Title
                            </th>
                            <th 
                                onClick={() => handleSort('company')}
                                className={sortField === 'company' ? `sorted-${sortDirection}` : ''}
                            >
                                Company
                            </th>
                            <th 
                                onClick={() => handleSort('location')}
                                className={sortField === 'location' ? `sorted-${sortDirection}` : ''}
                            >
                                Location
                            </th>
                            <th 
                                onClick={() => handleSort('platform')}
                                className={sortField === 'platform' ? `sorted-${sortDirection}` : ''}
                            >
                                Platform
                            </th>
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