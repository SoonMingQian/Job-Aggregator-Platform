from playwright.async_api import async_playwright
import json
from random import uniform
import asyncio
from redis import Redis
import uuid
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from kafka.errors import NoBrokersAvailable
from kafka import KafkaProducer
import time
import logging
from datetime import datetime

class JobsIEScraper:
    def __init__(self):
        self.MAX_JOBS = 100
        self.base_url = "https://www.jobs.ie"
        self.processed_urls = set()
        self.redis_client = self.init_redis()
        self.producer_analysis = self.create_kafka_producer()
        self.producer_storage = self.create_kafka_producer()

    def create_kafka_producer(self, retries=5):
        for attempt in range(retries):
            try:
                logger.info("Attempting to create Kafka producer (Attempt %d/%d)", attempt + 1, retries)
                return KafkaProducer(
                    bootstrap_servers=['kafka1:9092', 'kafka2:9093', 'kafka3:9094'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',
                    retries=3,
                    max_in_flight_requests_per_connection=1
                )
            except NoBrokersAvailable:
                if attempt < retries - 1:
                    logger.info(f"Failed to connect to Kafka. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise
    
    def init_redis(self):
        try:
            logger.info("Initializing Redis connection")
            redis_client = Redis(host='redis', port=6379, decode_responses=True)
            redis_client.ping()
            logger.info("Redis connection successful")
            return redis_client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None

    def generate_cache_key(self, title, job_location):
        return f"search:{title.lower()}:{job_location.lower()}:irishJobs"

    def get_cached_results(self, title, job_location):
        cache_key = self.generate_cache_key(title, job_location)
        cached_jobs = self.redis_client.smembers(cache_key)

        if cached_jobs:
            jobs = []
            for job_key in cached_jobs:
                job_data = self.redis_client.hgetall(job_key)
                jobs.append(job_data)
            return jobs
        return None

    def store_job_listing(self, job_data, title, job_location):
        try:
            job_key = job_data['jobId']
            self.redis_client.hmset(job_key, job_data)
            cache_key = self.generate_cache_key(title, job_location)
            self.redis_client.sadd(cache_key, job_key)
            self.redis_client.expire(job_key, 86400)
            self.redis_client.expire(cache_key, 86400)
            return job_key
        except Exception as e:
            logger.error(f"Error storing job listing: {e}")
            return None
    
    async def handle_cookie(self, page):
        try: 
            # Wait for cookie banner and click accept
            accept_button = await page.wait_for_selector('#ccmgt_explicit_accept', timeout=5000)
            if (accept_button):
                await accept_button.click()
                # Wait for cookie banner to disappear
                await page.wait_for_selector('#ccmgt_explicit_accept', state='hidden', timeout=5000)
                logger.info("Cookie accepted")
        except Exception as e:
            logger.warning("Cookie handling error: %s", str(e))

    async def extract_job_details(self, page):
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
                                    jobId: state.listingHeader?.listingData?.id || 'N/A',
                                    title: state.listingHeader?.listingData?.title || 'N/A',
                                    company: state.listingHeader?.companyData?.name || 'N/A',
                                    location: state.listingHeader?.listingData?.metaData?.location || 'N/A',
                                    work_type: state.listingHeader?.listingData?.metaData?.workType || 'N/A',
                                    jobDescription: state.textSections?.[0]?.content || 'N/A',
                                    posted_date: state.listingHeader?.listingData?.metaData?.onlineDate || 'N/A',
                                    applyLink: window.location.href
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
                logger.warning("Failed to extract state data")
                return None

            preloaded_state['apply_url'] = page.url
            logger.info("Extracted job: %s at %s", preloaded_state['title'], preloaded_state['company'])
            return preloaded_state

        except Exception as e:
            logger.error("Error extracting job details: %s", str(e))
            return None

    async def process_job_cards(self, page, processed_urls=None):
        jobs = []
        try:
            await page.wait_for_selector('article.res-1mik8pn')
            job_cards = await page.query_selector_all('article.res-1mik8pn')
            
            # Collect all job URLs
            job_urls = []
            for card in job_cards:
                try:
                    job_link = await card.query_selector('a.res-1oxi4gs')
                    if job_link:
                        href = await job_link.get_attribute('href')
                        full_url = f"{self.base_url}{href}"
                        if full_url not in processed_urls:
                            job_urls.append(full_url)
                except Exception as e:
                    logger.error(f"Error getting job URL: {e}")

            # Process jobs concurrently in batches
            batch_size = 3
            for i in range(0, len(job_urls), batch_size):
                batch = job_urls[i:i + batch_size]
                tasks = []
                
                for url in batch:
                    if url not in processed_urls:
                        tasks.append(self.process_single_job(page.context, url, processed_urls))
                
                if tasks:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in batch_results:
                        if result and not isinstance(result, Exception):
                            jobs.append(result)
                            logger.info(f"Added job: {result['title']}")
                    
                    logger.info(f"Processed batch {i//batch_size + 1}/{(len(job_urls) + batch_size - 1)//batch_size}")
                    await asyncio.sleep(1)

            logger.info(f"Collected {len(jobs)} jobs from this page")
            return jobs
        except Exception as e:
            logger.error(f"Error processing page: {e}")
            return []

    async def process_single_job(self, context, url, processed_urls=None):
        job_page = None
        try:
            job_page = await context.new_page()
            await job_page.goto(url, timeout=15000, wait_until='commit')
            
            job_data = await asyncio.wait_for(
                self.extract_job_details(job_page),
                timeout=10.0
            )
            
            if job_data:
                if processed_urls is not None:
                    processed_urls.add(url)
                self.processed_urls.add(url)
                logger.info(f"Processed job: {job_data['title']}")
                return job_data
                
        except Exception as e:
            logger.error(f"Error processing job {url}: {e}")
            return None
        finally:
            if job_page:
                await job_page.close()

    async def search_jobs(self, title, job_location, user_id):
        async with async_playwright() as p:
            browser = None
            try:            
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                all_jobs = []
                
                try:
                    page = await context.new_page()
                    search_url = f"{self.base_url}/jobs/{title}/in-{job_location}?radius=20&sort=2&action=sort_publish"
                    await page.goto(search_url)
                    await self.handle_cookie(page)
                    await page.wait_for_selector('.res-x8pfgj')

                    # Get total jobs count first
                    total_jobs_element = await page.query_selector('.at-facet-header-total-results')
                    if total_jobs_element:
                        total_jobs_text = await total_jobs_element.inner_text()
                        total_jobs = min(int(total_jobs_text.split()[0]), self.MAX_JOBS)  # Limit to MAX_JOBS
                        logger.info(f"\nNeed to collect {total_jobs} total jobs (limited to {self.MAX_JOBS} maximum)")
                        
                        # Calculate required pages (25 jobs per page)
                        required_pages = min((total_jobs + 24) // 25, (self.MAX_JOBS + 24) // 25)  # Limit pages based on MAX_JOBS
                        logger.info(f"Will process up to {required_pages} pages")

                        # Process first page
                        first_page_jobs = await self.process_job_cards(page, self.processed_urls)
                        # Only take up to total_jobs or MAX_JOBS from first page
                        for job in first_page_jobs[:min(total_jobs, self.MAX_JOBS)]:
                            formatted_job = {
                                'jobId': f"job:{job['jobId']}" if not job['jobId'].startswith('job:') else job['jobId'],
                                'title': job['title'],
                                'company': job['company'],
                                'location': job['location'],  
                                'jobDescription': job['jobDescription'],  
                                'applyLink': job['applyLink'], 
                                'timestamp': datetime.now().isoformat(),
                                'platform': "JobsIE"
                            }  
                            # Store in Redis
                            self.store_job_listing(formatted_job, title, job_location)
                            self.producer_analysis.send('analysis', value={
                                'jobId': job['jobId'], 
                                'jobDescription': job['jobDescription'],
                                'userId': user_id
                                })
                            self.producer_analysis.flush()

                            self.producer_storage.send('storage', value=formatted_job)
                            self.producer_storage.flush()
                            all_jobs.append(formatted_job)
                        jobs_collected = len(all_jobs)
                        logger.info(f"Collected {jobs_collected} jobs from page 1")

                        # Process additional pages if needed and haven't reached MAX_JOBS
                        page_num = 2
                        while len(all_jobs) < total_jobs and len(all_jobs) < self.MAX_JOBS and page_num <= required_pages:
                            logger.info(f"\nProcessing page {page_num} ({len(all_jobs)}/{self.MAX_JOBS} jobs collected)")
                            new_page = await context.new_page()
                            page_url = f"{self.base_url}/jobs/{title}/in-{job_location}?radius=20&page={page_num}&sort=2&action=sort_publish"
                            
                            try:
                                await new_page.goto(page_url, timeout=20000)
                                remaining_jobs = min(total_jobs - len(all_jobs), self.MAX_JOBS - len(all_jobs))
                                if remaining_jobs > 0:
                                    page_jobs = await self.process_job_cards(new_page, self.processed_urls)
                                    for job in page_jobs[:remaining_jobs]:
                                        formatted_job = {
                                            'jobId': f"job:{job['jobId']}" if not job['jobId'].startswith('job:') else job['jobId'],
                                            'title': job['title'],
                                            'company': job['company'],
                                            'location': job['location'],  
                                            'jobDescription': job['jobDescription'],  
                                            'applyLink': job['applyLink'], 
                                            'timestamp': datetime.now().isoformat(),
                                            'platform': "JobsIE"
                                        } 
                                        # Store in Redis
                                        self.store_job_listing(formatted_job, title, job_location)
                                        self.producer_analysis.send('analysis', value={
                                            'jobId': job['jobId'], 
                                            'jobDescription': job['jobDescription'],
                                            'userId': user_id
                                            })
                                        self.producer_analysis.flush()

                                        self.producer_storage.send('storage', value=formatted_job)
                                        self.producer_storage.flush()
                                        all_jobs.append(formatted_job)
                                    logger.info(f"Total jobs collected: {len(all_jobs)} of {total_jobs}")
                            except Exception as page_error:
                                logger.error(f"Error loading page {page_num}: {page_error}")
                            finally:
                                await new_page.close()
                            
                            page_num += 1

                        if all_jobs:
                            logger.info(f"Successfully collected and stored {len(all_jobs)} jobs")
                            return all_jobs  # Return the jobs directly
                        else:
                            logger.info("No jobs collected")
                            return []

                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                    return []
            except Exception as e:
                logger.error(f"Error in search_jobs: {str(e)}")
                return []
            finally:
                if browser:
                    await browser.close()

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
scraper = JobsIEScraper()

@app.route('/jobsie', methods=['GET'])
def jobsie():
    title = request.args.get('title')
    job_location = request.args.get('job_location')
    user_id = request.args.get('userId')
    
    if not all([title, job_location, user_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Use the scraper instance
        cached_results = scraper.get_cached_results(title, job_location)
        if cached_results:
            logger.info(f"Found {len(cached_results)} jobs in cache")
            return jsonify({
                "status": "success",
                "jobs": cached_results,
                "source": "cache"
            })

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraped_jobs = loop.run_until_complete(scraper.search_jobs(title, job_location, user_id))
            loop.close()

            if scraped_jobs and len(scraped_jobs) > 0:
                logger.info(f"Successfully scraped {len(scraped_jobs)} jobs")
                return jsonify({
                    "status": "success",
                    "jobs": scraped_jobs,
                    "total": len(scraped_jobs),
                    "source": "scraper"
                })
            
            logger.info("No jobs found")
            return jsonify({
                "status": "success",
                "jobs": [],
                "message": "No jobs found"
            })

        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    logger.info("Starting Jobs.ie Scraper Service")
    app.run(host='0.0.0.0', port=3003, debug=True)

