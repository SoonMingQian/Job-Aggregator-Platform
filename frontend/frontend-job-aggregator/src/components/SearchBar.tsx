import React, { useState, FormEvent, ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/SearchBar.css';

interface SearchBarProps {
    initialTitle?: string;
    initialLocation?: string;
    isLoading?: boolean;
    onSearch?: (title: string, location: string) => void;
    onFocus?: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({
    initialTitle = '',
    initialLocation = '',
    isLoading = false,
    onSearch,
    onFocus
}) => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        title: initialTitle,
        location: initialLocation
    });

    const getBrowserInfo = () => {
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

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSearch = (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        // If custom onSearch handler is provided, use it
        if (onSearch) {
            onSearch(formData.title, formData.location);
            return;
        }

        // Default search behavior - navigate to search page
        const browserInfo = getBrowserInfo();
        const searchParams = new URLSearchParams({
            title: formData.title,
            location: formData.location,
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

    return (
        <div className='search-section'>
            <h1>Find Your Jobs</h1>
            <form onSubmit={handleSearch} className='search-form'>
                <input
                    type='text'
                    name='title'
                    placeholder='Job Title'
                    value={formData.title}
                    onChange={handleInputChange}
                    onFocus={onFocus}
                    className='search-input'
                />
                <input
                    type='text'
                    name='location'
                    placeholder="Location..."
                    value={formData.location}
                    onChange={handleInputChange}
                    onFocus={onFocus}
                    className="search-input"
                />
                <button type="submit" className="search-button" disabled={isLoading}>
                    {isLoading ? 'Searching...' : 'Search'}
                </button>
            </form>
        </div>
    );
};

export default SearchBar;