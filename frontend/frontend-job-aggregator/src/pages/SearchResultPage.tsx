import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
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
    const { authFetch } = useAuthFetch();
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
    const [pendingRequests, setPendingRequests] = useState<Record<string, boolean>>({});
    const [sortField, setSortField] = useState<keyof Job | null>(null);
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

    const jobsPerPage: number = 20;
    const title: string = searchParams.get('title') || '';
    const location: string = searchParams.get('location') || '';

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

    const pollForScores = async (userId: string) => {
        try {
            console.log('Polling for match scores...');
            // Use authFetch here instead
            const matchResponse = await authFetch(
                `${import.meta.env.VITE_API_MATCHING_SERVICE}/api/redis/match/${userId}`
            );

            if (matchResponse.ok) {
                const matchScores = await matchResponse.json();
                console.log('Received match scores:', matchScores);

                setJobs(prevJobs => {
                    const updatedJobs = prevJobs.map(job => {
                        // Check if the key exists in matchScores object
                        const hasScore = Object.prototype.hasOwnProperty.call(matchScores, job.jobId);

                        return {
                            ...job,
                            // If the key exists, parse the score, otherwise keep undefined
                            matchScore: hasScore ? parseFloat(matchScores[job.jobId]) : undefined,
                            // Only show calculating if we don't have a score yet
                            isCalculating: !hasScore
                        };
                    });

                    // Only consider jobs with keys in matchScores as having received scores
                    const allScoresReceived = updatedJobs.every(job =>
                        Object.prototype.hasOwnProperty.call(matchScores, job.jobId)
                    );

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

            // Remove these lines - authFetch handles token validation
            // const token = Cookies.get('authToken');
            // if (!token) throw new Error('No token found');

            console.log('Fetching user profile...');
            // Use authFetch instead
            const profileResponse = await authFetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/userId`);

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
                    url: `${import.meta.env.VITE_API_JOBSIE}/jobsie?${new URLSearchParams({
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
                    url: `${import.meta.env.VITE_API_IRISHJOBS}/irishjobs?${new URLSearchParams({
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

                        // Special handling for 202 (request in progress)
                        if (response.status === 202) {
                            console.log(`${endpoint.name} reported request already in progress (202)`);

                            const data = await response.json();
                            console.log(`${endpoint.name} message:`, data.message);

                            // Update pending requests state to show user feedback
                            setPendingRequests(prev => ({
                                ...prev,
                                [endpoint.name]: true
                            }));

                            // Start polling for results with longer delays
                            const pollForResults = async (maxAttempts = 12, initialDelay = 10000) => {
                                for (let pollAttempt = 0; pollAttempt < maxAttempts; pollAttempt++) {
                                    // Exponential backoff - wait longer between each attempt
                                    const delay = initialDelay + (pollAttempt * 5000);
                                    console.log(`Polling ${endpoint.name} for results (attempt ${pollAttempt + 1}/${maxAttempts}) - waiting ${delay / 1000}s...`);

                                    await new Promise(resolve => setTimeout(resolve, delay));

                                    try {
                                        const pollResponse = await fetch(endpoint.url, {
                                            headers: {
                                                ...endpoint.headers,
                                                'X-Poll-Attempt': `${pollAttempt + 1}`,
                                                'Cache-Control': 'no-cache'
                                            }
                                        });

                                        if (pollResponse.status === 200) {
                                            const pollData = await pollResponse.json();

                                            if (pollData.jobs && Array.isArray(pollData.jobs)) {
                                                console.log(`${endpoint.name} poll successful! Got ${pollData.jobs.length} jobs`);
                                                const jobsWithMetadata = pollData.jobs.map((job: any) => {
                                                    // Check if matchScore is explicitly defined in the job object
                                                    const hasScore = Object.prototype.hasOwnProperty.call(job, 'matchScore');

                                                    return {
                                                        ...job,
                                                        // Only parse the score if it exists
                                                        matchScore: hasScore ? parseFloat(job.matchScore) : undefined,
                                                        // Only show calculating if we don't have a score
                                                        isCalculating: !hasScore
                                                    };
                                                });

                                                combinedJobs.push(...jobsWithMetadata);

                                                // Clear pending status
                                                setPendingRequests(prev => ({
                                                    ...prev,
                                                    [endpoint.name]: false
                                                }));

                                                return true; // Successfully got jobs
                                            }
                                        } else if (pollResponse.status === 202) {
                                            // Still processing, continue polling
                                            console.log(`${endpoint.name} still processing, will poll again in ${delay / 1000}s...`);
                                        } else {
                                            // Error or unexpected response
                                            console.error(`${endpoint.name} polling failed with status: ${pollResponse.status}`);
                                            break;
                                        }
                                    } catch (error) {
                                        console.error(`Error polling ${endpoint.name}:`, error);
                                        // Don't break on network errors, just continue polling
                                    }
                                }

                                console.log(`${endpoint.name} polling timed out after ${maxAttempts} attempts`);

                                // Clear pending status but with an error note
                                setPendingRequests(prev => ({
                                    ...prev,
                                    [endpoint.name]: false
                                }));

                                return false;
                            };

                            // Wait for polling to complete
                            const success = await pollForResults();

                            if (success) {
                                return; // Exit the retry loop
                            } else {
                                errors.push(`${endpoint.name}: Request is taking too long to process. The results may appear later.`);
                                return; // Exit anyway as we've done our best to wait
                            }
                        }

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
                            const jobsWithMetadata = data.jobs.map((job: any) => {
                                // Check if matchScore is explicitly defined in the job object
                                const hasScore = Object.prototype.hasOwnProperty.call(job, 'matchScore');

                                return {
                                    ...job,
                                    // Only parse the score if it exists
                                    matchScore: hasScore ? parseFloat(job.matchScore) : undefined,
                                    // Only show calculating if we don't have a score
                                    isCalculating: !hasScore
                                };
                            });

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
                            const profileResponse = await authFetch(`${import.meta.env.VITE_API_USER_SERVICE}/api/user/userId`);
                            const profileData = await profileResponse.json();
                            const userId = profileData.userId;

                            // Start polling here instead of inside fetchSearchResults
                            console.log('Starting polling for match scores from useEffect...');
                            // Use this in your interval
                            localPollInterval = setInterval(() => {
                                if (isActive) {
                                    // Remove token parameter since authFetch handles it
                                    debouncedPollForScores(userId);
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
    }, [title, location, authFetch]); // Keep this dependency array

    const toggleJobDescription = (jobId: string): void => {
        setExpandedJob(prevId => prevId === jobId ? null : jobId);
    }

    const handleBackClick = (): void => {
        navigate('/');
    };

    // Sort jobs based on current sort settings
    const sortedJobs = [...jobs].sort((a, b) => {
        if (sortField === null) return 0;

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

    // Then use sortedJobs for pagination instead of jobs
    const currentJobs = sortedJobs.slice(
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
                    {/* Pending requests indicator */}
                    {Object.keys(pendingRequests).some(key => pendingRequests[key]) && (
                        <div className="pending-requests-banner">
                            <div className="mini-loader"></div>
                            <div className="pending-text">
                                <strong>Scraping in progress:</strong> Still collecting jobs from {Object.keys(pendingRequests)
                                    .filter(key => pendingRequests[key])
                                    .join(', ')}
                                <br />
                                <span className="pending-subtext">Web scraping typically takes 1-3 minutes. Results will appear automatically when ready.</span>
                            </div>
                        </div>
                    )}

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
                                            style={{ marginLeft: '15px' }}
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
                                            // Show a message that this could take a while
                                            alert("Restarting search. Web scraping can take 1-3 minutes to complete.");
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
                                        <th onClick={() => handleSort('title')}
                                            className={sortField === 'title' ? `sorted-${sortDirection}` : ''}
                                        >
                                            Title
                                        </th>
                                        <th onClick={() => handleSort('company')}
                                            className={sortField === 'company' ? `sorted-${sortDirection}` : ''}
                                        >
                                            Company
                                        </th>
                                        <th onClick={() => handleSort('location')}
                                            className={sortField === 'location' ? `sorted-${sortDirection}` : ''}
                                        >
                                            Location
                                        </th>
                                        <th
                                            onClick={() => handleSort('matchScore')}
                                            className={sortField === 'matchScore' ? `sorted-${sortDirection}` : ''}
                                        >
                                            Match Score
                                        </th>
                                        <th onClick={() => handleSort('platform')} className={sortField === 'platform' ? `sorted-${sortDirection}` : ''}
                                        >
                                            Platform
                                        </th>
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
                                                    {job.isCalculating ? (
                                                        <span className="calculating">Calculating...</span>
                                                    ) : (
                                                        `${job.matchScore?.toFixed(2) || '0.00'}%`
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
                            <svg className="no-results-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="11" cy="11" r="8"></circle>
                                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                            </svg>
                            <h3>No jobs found</h3>
                            <p>We couldn't find any jobs matching "{title}" in {location}</p>

                            <ul className="suggestions">
                                <li>Check the spelling of your search terms</li>
                                <li>Try using more general keywords</li>
                                <li>Try searching without location</li>
                                <li>Consider alternative job titles</li>
                            </ul>

                            <button
                                className="search-again-button"
                                onClick={() => {
                                    const searchInput = document.querySelector('input[type="text"]') as HTMLInputElement;
                                    if (searchInput) {
                                        searchInput.focus();
                                    }
                                }}
                            >
                                Modify Search
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default SearchResultPage;