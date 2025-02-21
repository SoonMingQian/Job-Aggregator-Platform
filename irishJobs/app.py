from playwright.async_api import async_playwright
import json
from random import uniform
import asyncio
from redis import Redis
import uuid

async def handle_cookie(page):
    try: 
        # Wait for cookie banner and click accept
        accept_button = await page.wait_for_selector('#ccmgt_explicit_accept', timeout=5000)
        if (accept_button):
            await accept_button.click()
            # Wait for cookie banner to disappear
            await page.wait_for_selector('#ccmgt_explicit_accept', state='hidden', timeout=5000)
            print("Cookie accepted")
    except Exception as e:
        print(f"Cookie handling error: {e}")

async def open_page(context, title, location, page_num):
    new_page = await context.new_page()
    page_url = f"https://www.irishjobs.ie/jobs/{title}/in-{location}?radius=30&page={page_num}&sort=2&action=sort_publish"
    await new_page.goto(page_url)
    print(f"Opened page {page_num}")
    return new_page

async def extract_job_details(page):
    try:
        # Get the preloaded state data immediately without waiting
        preloaded_state = await page.evaluate('''() => {
            return new Promise((resolve) => {
                // Function to check state
                const checkState = () => {
                    try {
                        const state = window.__PRELOADED_STATE__?.JobAdContent?.props;
                        if (state) {
                            resolve({
                                title: state.listingHeader?.listingData?.title || 'N/A',
                                company: state.listingHeader?.companyData?.name || 
                                        state.companyData?.name || 'N/A',  // Check both locations
                                location: state.listingHeader?.listingData?.metaData?.location || 'N/A',
                                work_type: state.listingHeader?.listingData?.metaData?.workType || 'N/A',
                                description: state.textSections?.[0]?.content || 'N/A',
                                posted_date: state.listingHeader?.listingData?.metaData?.onlineDate || 'N/A'
                            });
                            return;
                        }
                        // Retry after 100ms if state not found
                        setTimeout(checkState, 100);
                    } catch (e) {
                        console.error('Error checking state:', e);
                        resolve(null);
                    }
                };
                
                // Start checking
                checkState();
                
                // Timeout after 5 seconds
                setTimeout(() => resolve(null), 5000);
            });
        }''')

        if not preloaded_state:
            print("Failed to extract state data")
            return None

        preloaded_state['apply_url'] = page.url
        print(f"Extracted job: {preloaded_state['title']} at {preloaded_state['company']}")
        return preloaded_state

    except Exception as e:
        print(f"Error extracting job details: {e}")
        return None

async def process_job_cards(page, processed_urls=None):
    if processed_urls is None:
        processed_urls = set()
    
    jobs = []
    try:
        await page.wait_for_selector('article.res-1p8f8en')
        job_cards = await page.query_selector_all('article.res-1p8f8en')
        
        # Collect all job URLs
        job_urls = []
        for card in job_cards:
            try:
                job_link = await card.query_selector('a.res-1foik6i')
                if job_link:
                    href = await job_link.get_attribute('href')
                    full_url = f"https://www.irishjobs.ie{href}"
                    if full_url not in processed_urls:
                        job_urls.append(full_url)
            except Exception as e:
                print(f"Error getting job URL: {e}")

        # Process jobs concurrently in batches
        batch_size = 3
        for i in range(0, len(job_urls), batch_size):
            batch = job_urls[i:i + batch_size]
            tasks = []
            
            for url in batch:
                if url not in processed_urls:
                    tasks.append(process_single_job(page.context, url, processed_urls))
            
            if tasks:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in batch_results:
                    if result and not isinstance(result, Exception):
                        jobs.append(result)
                        print(f"Added job: {result['title']}")
                
                print(f"Processed batch {i//batch_size + 1}/{(len(job_urls) + batch_size - 1)//batch_size}")
                await asyncio.sleep(1)

        print(f"Collected {len(jobs)} jobs from this page")
        return jobs
    except Exception as e:
        print(f"Error processing page: {e}")
        return []

async def process_single_job(context, url, processed_urls):
    job_page = None
    try:
        job_page = await context.new_page()
        await job_page.goto(url, timeout=15000, wait_until='commit')
        
        job_data = await asyncio.wait_for(
            extract_job_details(job_page),
            timeout=10.0
        )
        
        if job_data:
            processed_urls.add(url)
            print(f"Processed job: {job_data['title']}")
            return job_data
            
    except Exception as e:
        print(f"Error processing job {url}: {e}")
        return None
    finally:
        if job_page:
            await job_page.close()

async def search_jobs(title, location):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        all_jobs = []
        processed_urls = set()

        try:
            page = await context.new_page()
            search_url = f"https://www.irishjobs.ie/jobs/{title}/in-{location}?radius=30&sort=2&action=sort_publish"
            await page.goto(search_url)
            await handle_cookie(page)
            await page.wait_for_selector('.res-14njlc6')

            # Get total jobs count first
            total_jobs_element = await page.query_selector('.at-facet-header-total-results')
            if total_jobs_element:
                total_jobs_text = await total_jobs_element.inner_text()
                total_jobs = int(total_jobs_text.split()[0])  # Extract number from text
                print(f"\nNeed to collect {total_jobs} total jobs")
                
                # Calculate required pages (25 jobs per page)
                required_pages = (total_jobs + 24) // 25  # Round up division
                print(f"Will process {required_pages} pages")

                # Process first page
                first_page_jobs = await process_job_cards(page, processed_urls)
                # Only take up to total_jobs from first page
                all_jobs.extend(first_page_jobs[:total_jobs])
                jobs_collected = len(all_jobs)
                print(f"Collected {jobs_collected} jobs from page 1")

                # Process additional pages if needed
                page_num = 2
                while len(all_jobs) < total_jobs and page_num <= required_pages:
                    print(f"\nProcessing page {page_num}")
                    new_page = await context.new_page()
                    page_url = f"https://www.irishjobs.ie/jobs/{title}/in-{location}?radius=30&page={page_num}&sort=2&action=sort_publish"
                    
                    try:
                        await new_page.goto(page_url, timeout=20000)
                        remaining_jobs = total_jobs - len(all_jobs)
                        if remaining_jobs > 0:
                            page_jobs = await process_job_cards(new_page, processed_urls)
                            all_jobs.extend(page_jobs[:remaining_jobs])
                            print(f"Total jobs collected: {len(all_jobs)} of {total_jobs}")
                    except Exception as page_error:
                        print(f"Error loading page {page_num}: {page_error}")
                    finally:
                        await new_page.close()
                    
                    page_num += 1

                # Save collected jobs
                if all_jobs:
                    with open('jobs.json', 'w', encoding='utf-8') as f:
                        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
                    print(f"\nSuccessfully collected {len(all_jobs)} jobs")
                    print("Results saved to jobs.json")
                else:
                    print("\nNo jobs collected to save")

            await asyncio.get_event_loop().run_in_executor(None, input, "\nPress Enter to close the browser...")
            
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            await browser.close()

"""Redis"""
def init_redis():
    try:
        redis_client = Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        # Test connection
        redis_client.ping()
        return redis_client
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return None

def generate_job_id(job_data):
    unique_string = f"{job_data['company']}:{job_data['title']}:{job_data['location']}:{job_data['posted_date']}"
    job_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
    return f"job:{job_id}"

if __name__ == "__main__":
    asyncio.run(search_jobs("Software Developer", "galway"))