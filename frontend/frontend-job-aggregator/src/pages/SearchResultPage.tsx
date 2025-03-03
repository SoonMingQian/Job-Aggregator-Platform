import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
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
    isCalculating?: boolean;
    platform: string;
}

interface SearchHistoryItem {
    id: string;
    title: string;
    location: string;
    timestamp: string;
}

// Add this utility function at the top of your file
const debounce = (func: Function, delay: number) => {
    let timeoutId: NodeJS.Timeout;
    return (...args: any[]) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
};

const SearchResultPage: React.FC = (): JSX.Element => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    const [jobs, setJobs] = useState<Job[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>('');
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [expandedJob, setExpandedJob] = useState<string | null>(null);
    const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);
    const [isRequesting, setIsRequesting] = useState<boolean>(false);
    const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
    const [showSearchHistory, setShowSearchHistory] = useState(false);
    const searchContainerRef = useRef<HTMLDivElement>(null);

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

    // Then use a debounced version of your pollForScores
    const debouncedPollForScores = debounce(pollForScores, 500);

    // In SearchResultPage.tsx, modify the fetchSearchResults function

    const fetchSearchResults = async (): Promise<Job[]> => {
        // Prevent multiple concurrent requests for the same search
        if (isRequesting) {
            console.log('Search already in progress, skipping duplicate request');
            return [];
        }

        try {
            setIsRequesting(true);
            console.log('Starting search for:', { title, location });
            setIsLoading(true);
            const token = Cookies.get('authToken');
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

            // Define all API endpoints with their metadata
            const apiEndpoints = [
                {
                    name: 'jobsie',
                    url: `http://127.0.0.1:3002/jobsie?${new URLSearchParams({
                        title: title,
                        job_location: location,
                        userId,
                        platform: browserInfo.platform,
                        language: browserInfo.language,
                        timezone: browserInfo.timezone,
                        screen_resolution: browserInfo.screen_resolution,
                        color_depth: browserInfo.color_depth,
                        device_memory: browserInfo.device_memory,
                        hardware_concurrency: browserInfo.hardware_concurrency,
                        user_agent: browserInfo.user_agent
                    })}`,
                    headers: { 'Accept': 'application/json', 'Cache-Control': 'no-store' },
                },
                {
                    name: 'irishjobs',
                    url: `http://127.0.0.1:3003/irishjobs?${new URLSearchParams({
                        title: title,
                        job_location: location,
                        userId,
                        platform: browserInfo.platform,
                        language: browserInfo.language,
                        timezone: browserInfo.timezone,
                        screen_resolution: browserInfo.screen_resolution,
                        color_depth: browserInfo.color_depth,
                        device_memory: browserInfo.device_memory,
                        hardware_concurrency: browserInfo.hardware_concurrency,
                        user_agent: browserInfo.user_agent
                    })}`,
                    headers: { 'Accept': 'application/json', 'Cache-Control': 'no-store' },
                }
                // Add more API endpoints as needed
            ];

            console.log('Making API calls to job search endpoints...');

            // Create an array to store results as they come in
            const combinedJobs: Job[] = [];
            const errors: string[] = [];

            // Function to process a single API endpoint with retries
            const processEndpoint = async (endpoint: typeof apiEndpoints[0], retries = 2): Promise<void> => {
                for (let attempt = 0; attempt <= retries; attempt++) {
                    try {
                        console.log(`Fetching from ${endpoint.name} (attempt ${attempt + 1}/${retries + 1})`);
                        const response = await fetch(endpoint.url, { headers: endpoint.headers });

                        if (!response.ok) {
                            throw new Error(`${endpoint.name} returned status ${response.status}`);
                        }

                        const data = await response.json();

                        if (data.error) {
                            throw new Error(`${endpoint.name} error: ${data.error}`);
                        }

                        console.log(`${endpoint.name} returned ${data.jobs?.length || 0} jobs`);

                        // Add jobs to the combined list
                        if (data.jobs && Array.isArray(data.jobs)) {
                            const jobsWithMetadata = data.jobs.map((job: any) => ({
                                ...job,
                                // Only set matchScore to undefined if it doesn't already exist
                                matchScore: job.matchScore !== undefined ? parseFloat(job.matchScore) : undefined,
                                // Only set isCalculating if matchScore doesn't exist
                                isCalculating: job.matchScore === undefined
                            }));

                            combinedJobs.push(...jobsWithMetadata);
                        }

                        // Success, exit the retry loop
                        return;

                    } catch (error) {
                        // If we've run out of retries, record the error
                        if (attempt === retries) {
                            errors.push(`${endpoint.name}: ${error instanceof Error ? error.message : String(error)}`);
                        } else {
                            // Wait before retrying (exponential backoff)
                            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
                        }
                    }
                }
            };

            // Process all endpoints with a concurrency limit
            const concurrencyLimit = 2; // Number of simultaneous requests

            // Process in batches to control concurrency
            for (let i = 0; i < apiEndpoints.length; i += concurrencyLimit) {
                const batch = apiEndpoints.slice(i, i + concurrencyLimit);
                await Promise.all(batch.map(endpoint => processEndpoint(endpoint)));
            }

            console.log('All API requests completed');
            console.log('Total combined jobs:', combinedJobs.length);

            // Set the error if any endpoint failed
            if (errors.length > 0) {
                setError(`Some search sources failed: ${errors.join(', ')}`);
            }

            // Update the jobs state with whatever was successfully fetched
            setJobs(combinedJobs);

            return combinedJobs

        } catch (error) {
            console.error('Search error:', error);
            setError(error instanceof Error ? error.message : 'Failed to fetch results');
            return [];
        } finally {
            setIsLoading(false);
            setIsRequesting(false); // Reset the requesting flag
        }
    };

    useEffect(() => {
        console.log('SearchResultPage mounted/updated with:', { title, location });
        let isActive = true;
        let localPollInterval: NodeJS.Timeout | null = null;

        // Load search history from cookies
        const loadSearchHistory = () => {
            const historyString = Cookies.get('searchHistory');
            console.log("Retrieved search history from cookies:", historyString);
            if (historyString) {
                try {
                    const history = JSON.parse(historyString);
                    console.log("Parsed history:", history);
                    setSearchHistory(Array.isArray(history) ? history : []);
                } catch (e) {
                    console.error('Error parsing search history from cookie:', e);
                    setSearchHistory([]);
                }
            }
        };
        
        loadSearchHistory();

        // Add click outside handler for search history
        const handleClickOutside = (event: MouseEvent) => {
            if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
                setShowSearchHistory(false);
            }
        };
        
        document.addEventListener('mousedown', handleClickOutside);

        if (title || location) {
            // Save this search to history if it came from URL params
            if (title || location) {
                const saveCurrentSearch = () => {
                    const id = Date.now().toString();
                    const timestamp = new Date().toISOString();
                    
                    const newHistoryItem: SearchHistoryItem = {
                        id,
                        title,
                        location,
                        timestamp
                    };
                    
                    // Get existing history
                    const historyString = Cookies.get('searchHistory');
                    let existingHistory: SearchHistoryItem[] = [];
                    
                    if (historyString) {
                        try {
                            existingHistory = JSON.parse(historyString);
                            if (!Array.isArray(existingHistory)) existingHistory = [];
                        } catch (e) {
                            console.error('Error parsing existing history:', e);
                        }
                    }
                    
                    // Only add if it doesn't already exist
                    if (!existingHistory.some(item => item.title === title && item.location === location)) {
                        const updatedHistory = [
                            newHistoryItem,
                            ...existingHistory.slice(0, 5)
                        ];
                        
                        try {
                            Cookies.set('searchHistory', JSON.stringify(updatedHistory), {
                                expires: 30,
                                sameSite: 'strict',
                                secure: window.location.protocol === 'https:',
                            });
                            setSearchHistory(updatedHistory);
                        } catch (e) {
                            console.error('Error saving search history:', e);
                        }
                    }
                };
                
                saveCurrentSearch();
            }

            (async () => {
                if (!isActive) return;

                try {
                    const fetchedJobs = await fetchSearchResults();

                    // Only start polling after jobs are fetched successfully
                    if (isActive && fetchedJobs && fetchedJobs.length > 0) {
                        const needScores = fetchedJobs.some(job => job.matchScore === undefined);
                        if (needScores) {
                            const token = Cookies.get('authToken');
                            const profileResponse = await fetch('http://localhost:8081/api/user/userId', {
                                headers: { 'Authorization': token as string }
                            });
                            const profileData = await profileResponse.json();
                            const userId = profileData.userId;

                            // Start polling here instead of inside fetchSearchResults
                            console.log('Starting polling for match scores from useEffect...');
                            // Use this in your interval
                            localPollInterval = setInterval(() => {
                                if (isActive) {
                                    debouncedPollForScores(userId, token as string);
                                }
                            }, 2000);
                            setPollInterval(localPollInterval);
                        }
                    } else {
                        console.log('All jobs already have match scores')
                    }
                } catch (error) {
                    console.error('Search failed:', error);
                }
            })();
        }

        // Use a more robust cleanup function
        return () => {
            console.log('Cleaning up SearchResultPage');
            isActive = false;

            if (localPollInterval) {
                console.log('Clearing local poll interval');
                clearInterval(localPollInterval);
            }

            if (pollInterval) {
                console.log('Clearing state poll interval');
                clearInterval(pollInterval);
                setPollInterval(null);
            }
            
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [title, location]); // Keep this dependency array

    const toggleJobDescription = (jobId: string): void => {
        setExpandedJob(prevId => prevId === jobId ? null : jobId);
    }

    const handleBackClick = (): void => {
        navigate('/');
    };

    const currentJobs: Job[] = jobs.slice(
        (currentPage - 1) * jobsPerPage,
        currentPage * jobsPerPage
    );

    const handleSearch = (title: string, location: string) => {
        // Save this search to history
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
                ).slice(0, 9)
            ];
            
            setSearchHistory(updatedHistory);
            
            try {
                Cookies.set('searchHistory', JSON.stringify(updatedHistory), {
                    expires: 30,
                    sameSite: 'strict',
                    secure: window.location.protocol === 'https:',
                });
                console.log("Saved search history:", Cookies.get('searchHistory'));
            } catch (e) {
                console.error('Error saving search history to cookie:', e);
            }
        };
        
        // Save search first
        saveSearchHistory(title, location);
        
        // Hide search history dropdown
        setShowSearchHistory(false);
        
        // Get browser info
        const browserInfo = {
            platform: navigator.platform || 'unknown',
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen_resolution: `${window.screen.width}x${window.screen.height}`,
            color_depth: window.screen.colorDepth.toString(),
            device_memory: ((navigator as any).deviceMemory || '8').toString(),
            hardware_concurrency: navigator.hardwareConcurrency.toString(),
            user_agent: navigator.userAgent
        };

        // Build search parameters
        const params = new URLSearchParams({
            title,
            location,
            platform: browserInfo.platform,
            language: browserInfo.language,
            timezone: browserInfo.timezone,
            screen_resolution: browserInfo.screen_resolution,
            color_depth: browserInfo.color_depth,
            device_memory: browserInfo.device_memory,
            hardware_concurrency: browserInfo.hardware_concurrency,
            user_agent: browserInfo.user_agent
        });

        // Navigate with new search parameters
        navigate(`/search?${params}`);
    };

    const clearSearchHistory = () => {
        setSearchHistory([]);
        Cookies.remove('searchHistory');
    };

    return (
        <div className="main-page">
            <div className='search-results-header'>
                <button onClick={handleBackClick} className="back-button">
                    Back to Search
                </button>
            </div>

            <div className='search-container' ref={searchContainerRef}>
                <SearchBar
                    initialTitle={title}
                    initialLocation={location}
                    isLoading={isLoading}
                    onSearch={handleSearch}
                    onFocus={() => setShowSearchHistory(true)} // Add this prop
                />

                {/* Add search history dropdown */}
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

            {isLoading ? (
                <div className="loading-container">
                    <div className="loader"></div>
                </div>
            ) : (
                <>
                    {/* Always show error message if there is an error */}
                    {error && (
                        <div className="error-container">
                            {jobs.length > 0 ? (
                                // Partial error - some jobs were successfully fetched
                                <>
                                    <div className="error-message partial-error">
                                        <span className="error-title">Some results couldn't be loaded:</span>
                                        {error}
                                        <button 
                                            className="retry-button" 
                                            style={{marginLeft: '15px'}}
                                            onClick={() => {
                                                setError('');
                                                setIsLoading(true);
                                                fetchSearchResults().catch(err => {
                                                    console.error("Retry failed:", err);
                                                    setError(err instanceof Error ? err.message : "Failed to fetch results on retry");
                                                });
                                            }}
                                        >
                                            Retry Failed Sources
                                        </button>
                                    </div>
                                </>
                            ) : (
                                // Complete error - no jobs were fetched
                                <>
                                    <div className="error-message">
                                        <span className="error-title">Error fetching job results:</span>
                                        {error}
                                    </div>
                                    <button 
                                        className="retry-button"
                                        onClick={() => {
                                            setError('');
                                            setIsLoading(true);
                                            fetchSearchResults().catch(err => {
                                                console.error("Retry failed:", err);
                                                setError(err instanceof Error ? err.message : "Failed to fetch results on retry");
                                            });
                                        }}
                                    >
                                        Retry Search
                                    </button>
                                </>
                            )}
                        </div>
                    )}
                    
                    {/* Always show jobs section if there are jobs */}
                    {jobs.length > 0 && (
                        <div className='jobs-section'>
                            <div className="search-results-heading">
                                Search Results for <span className="search-term">"{title}"</span> in <span className="location-term">{location}</span>
                                <span className="search-results-count">{jobs.length} jobs found</span>
                            </div>
                            
                            <table className='jobs-table'>
                                <thead>
                                    <tr>
                                        <th>Title</th>
                                        <th>Company</th>
                                        <th>Location</th>
                                        <th>Match Score</th>
                                        <th>Platform</th>
                                        <th>Action</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {currentJobs.map((job: Job) => (
                                        <React.Fragment key={job.jobId}>
                                            {/* Job rows as before */}
                                            <tr className='job-row' onClick={() => toggleJobDescription(job.jobId)}>
                                                <td>{job.title}</td>
                                                <td>{job.company}</td>
                                                <td>{job.location}</td>
                                                <td>
                                                    {job.matchScore === undefined ? (
                                                        <span className="calculating">Calculating...</span>
                                                    ) : (
                                                        `${job.matchScore.toFixed(2)}%`
                                                    )}
                                                </td>
                                                <td>{job.platform}</td>
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

                            {jobs.length > 0 && (
                                <Pagination
                                    currentPage={currentPage}
                                    totalPages={Math.ceil(jobs.length / jobsPerPage)}
                                    onPageChange={setCurrentPage}
                                />
                            )}
                        </div>
                    )}
                    
                    {!isLoading && jobs.length === 0 && !error && (
                        <div className="no-results-message">
                            <h3>No jobs found for your search</h3>
                            <p>Try adjusting your search terms or location for more results.</p>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default SearchResultPage;