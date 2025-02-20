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
        if accept_button:
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
        # Wait longer for initial page load
        await page.wait_for_load_state('domcontentloaded', timeout=15000)
        
        # Check if state exists and wait for it
        await page.wait_for_function('''() => {
            if (!window.__PRELOADED_STATE__) return false;
            if (!window.__PRELOADED_STATE__.JobAdContent) return false;
            if (!window.__PRELOADED_STATE__.JobAdContent.props) return false;
            return true;
        }''', timeout=15000)

        # Get the preloaded state data with error checking
        preloaded_state = await page.evaluate('''() => {
            try {
                const state = window.__PRELOADED_STATE__.JobAdContent.props;
                if (!state) return null;
                
                return {
                    title: state.listingHeader?.listingData?.title || 'N/A',
                    company: state.companyData?.name || 'N/A',
                    location: state.listingHeader?.listingData?.metaData?.location || 'N/A',
                    contract_type: state.listingHeader?.listingData?.metaData?.contractType || 'N/A',
                    work_type: state.listingHeader?.listingData?.metaData?.workType || 'N/A',
                    description: state.textSections?.[0]?.content || 'N/A',
                    posted_date: state.listingHeader?.listingData?.metaData?.onlineDate || 'N/A'
                };
            } catch (e) {
                console.error('Error parsing state:', e);
                return null;
            }
        }''')

        if not preloaded_state:
            print("Failed to extract state data")
            return None

        # Add the URL to the data
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
        print(f"Found {len(job_cards)} job cards")

        for i, card in enumerate(job_cards, 1):
            retries = 3
            for attempt in range(retries):
                try:
                    job_link = await card.query_selector('a.res-1foik6i')
                    if job_link:
                        href = await job_link.get_attribute('href')
                        full_url = f"https://www.irishjobs.ie{href}"
                        
                        # Skip if URL already processed
                        if full_url in processed_urls:
                            print(f"Skipping already processed job {i}")
                            break
                        
                        job_page = await page.context.new_page()
                        try:
                            await job_page.goto(full_url, timeout=15000)
                            await job_page.wait_for_load_state('domcontentloaded', timeout=10000)
                            
                            job_data = await asyncio.wait_for(
                                extract_job_details(job_page),
                                timeout=10.0
                            )
                            if job_data:
                                jobs.append(job_data)
                                processed_urls.add(full_url)  # Add URL to processed set
                                print(f"Processed job {i}/{len(job_cards)}: {job_data['title']}")
                                break
                        except asyncio.TimeoutError:
                            print(f"Timeout extracting details for job {i}, attempt {attempt + 1}/{retries}")
                        finally:
                            await job_page.close()
                    
                except Exception as e:
                    print(f"Error processing job card {i}, attempt {attempt + 1}/{retries}: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)
                    else:
                        break

        return jobs
    except Exception as e:
        print(f"Error processing page: {e}")
        return []

async def search_jobs(title, location):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        all_jobs = []
        processed_urls = set()  # Track all processed URLs

        try:
            page = await context.new_page()
            search_url = f"https://www.irishjobs.ie/jobs/{title}/in-{location}?radius=30&sort=2&action=sort_publish"
            await page.goto(search_url)
            await handle_cookie(page)
            await page.wait_for_selector('.res-14njlc6')

            # Process first page with URL tracking
            first_page_jobs = await process_job_cards(page, processed_urls)
            all_jobs.extend(first_page_jobs)
            print(f"Processed {len(first_page_jobs)} jobs from page 1")

            # Get pagination info
            page_numbers = await page.query_selector_all('.res-vurnku span[aria-hidden="true"]')
            if page_numbers:
                numbers = []
                for num in page_numbers:
                    text = await num.inner_text()
                    try:
                        if text.strip():
                            numbers.append(int(text))
                    except ValueError:
                        continue
                
                if numbers:
                    last_page = max(numbers)
                    print(f"Total pages: {last_page}")

                    # Process remaining pages with URL tracking
                    for page_num in range(2, last_page + 1):
                        try:
                            print(f"\nProcessing page {page_num}")
                            new_page = await context.new_page()
                            page_url = f"https://www.irishjobs.ie/jobs/{title}/in-{location}?radius=30&page={page_num}&sort=2&action=sort_publish"
                            
                            # Try to load the page with timeout
                            try:
                                await new_page.goto(page_url, timeout=20000)  # 20 second timeout
                                page_jobs = await process_job_cards(new_page, processed_urls)
                                all_jobs.extend(page_jobs)
                                print(f"Processed {len(page_jobs)} jobs from page {page_num}")
                            except Exception as page_error:
                                print(f"Error loading page {page_num}: {page_error}")
                            finally:
                                await new_page.close()
                                
                        except Exception as e:
                            print(f"Error processing page {page_num}: {e}")
                            continue

            # Save all collected jobs
            if all_jobs:  # Only save if we have jobs
                with open('jobs.json', 'w', encoding='utf-8') as f:
                    json.dump(all_jobs, f, indent=2, ensure_ascii=False)
                print(f"\nTotal jobs collected: {len(all_jobs)}")
                print("Results saved to jobs.json")
            else:
                print("\nNo jobs collected to save")
            
            # Keep browser open for inspection
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
    asyncio.run(search_jobs("accountant", "galway"))