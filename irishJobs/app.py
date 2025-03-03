from playwright.async_api import async_playwright
import json
from random import uniform
import asyncio
from redis import Redis
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka.errors import NoBrokersAvailable
from kafka import KafkaProducer
import time
import logging
from datetime import datetime

class IrishJobsScraper:
    def __init__(self):
        self.MAX_JOBS = 100
        self.base_url = "https://www.irishjobs.ie"
        self.processed_urls = set()
        self.redis_client = self.init_redis()
        self.producer_analysis = self.create_kafka_producer()
        self.producer_storage = self.create_kafka_producer()

    def create_kafka_producer(self, retries=5):
        for attempt in range(retries):
            try:
                logger.info(f"Attempting to create Kafka producer (Attempt {attempt + 1}/{retries})")
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
        
    def generate_job_id(self, job_data):
        unique_string = f"{job_data['company']}:{job_data['title']}:{job_data['location']}:{job_data['posted_date']}"
        job_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
        return f"job:{job_id}"
    
    def generate_cache_key(self, title, job_location):
        return f"search:{title.lower()}:{job_location.lower()}:irishJobs"

    def get_cached_results(self, title, job_location, user_id):
        cache_key = self.generate_cache_key(title, job_location)
        cached_jobs = self.redis_client.smembers(cache_key)

        if cached_jobs:
            jobs = []
            for job_key in cached_jobs:
                job_data = self.redis_client.hgetall(job_key)

                if user_id:
                    # Try both with and without the job: prefix to handle all cases
                    match_key = f"match:{user_id}"
                    match_score = self.redis_client.hget(match_key, job_key) 
                    
                    if match_score is not None:
                        logger.info(f"Found match score {match_score} for job {job_key}")
                        job_data['matchScore'] = float(match_score)
                jobs.append(job_data)
                logger.info(f"Found {len(jobs)} jobs in cache" + 
                   (f" with {sum(1 for job in jobs if 'matchScore' in job)} match scores" if user_id else ""))
            return jobs
        return None

    def store_job_listing(self, job_data, title, job_location):
        try:
            job_key = job_data['jobId']
            self.redis_client.hmset(job_key, job_data)
            cache_key = f"search:{title.lower()}:{job_location.lower()}:irishJobs"
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
            if accept_button:
                await accept_button.click()
                # Wait for cookie banner to disappear
                await page.wait_for_selector('#ccmgt_explicit_accept', state='hidden', timeout=5000)
                logger.info("Cookie accepted")
        except Exception as e:
            logger.warning(f"Cookie handling error: {e}")

    async def extract_job_details(self, page):
        try:
            # Get the preloaded state data immediately without waiting
            preloaded_state = await page.evaluate('''() => {
                return new Promise((resolve) => {
                    const checkState = () => {
                        try {
                            const state = window.__PRELOADED_STATE__?.JobAdContent?.props;
                            if (state) {
                                resolve({
                                    title: state.listingHeader?.listingData?.title || 'N/A',
                                    company: state.listingHeader?.companyData?.name || 
                                            state.companyData?.name || 'N/A',
                                    location: state.listingHeader?.listingData?.metaData?.location || 'N/A',  // Changed from job_location
                                    jobDescription: state.textSections?.[0]?.content || 'N/A',  // Changed from description
                                    applyLink: window.location.href,  // Changed from apply_url
                                    posted_date: state.listingHeader?.listingData?.metaData?.onlineDate || 'N/A'
                                });
                                return;
                            }
                            setTimeout(checkState, 100);
                        } catch (e) {
                            console.error('Error checking state:', e);
                            resolve(null);
                        }
                    };
                    checkState();
                    setTimeout(() => resolve(null), 5000);
                });
            }''')

            if not preloaded_state:
                logger.warning("Failed to extract state data")
                return None

            logger.info(f"Extracted job: {preloaded_state['title']} at {preloaded_state['company']}")
            return preloaded_state

        except Exception as e:
            logger.error(f"Error extracting job details: {e}")
            return None

    async def process_job_cards(self, page, url, processed_urls=None):
        jobs = []
        try:
            await page.wait_for_selector('article.res-sfoyn7', timeout=5000)
            job_cards = await page.query_selector_all('article.res-sfoyn7')
            
            # Collect all job URLs
            job_urls = []
            for card in job_cards:
                try:
                    job_link = await card.query_selector('a.res-1foik6i')
                    if job_link:
                        href = await job_link.get_attribute('href')
                        full_url = f"{self.base_url}{href}"
                        if full_url not in self.processed_urls:
                            job_urls.append(full_url)
                except Exception as e:
                    logger.error(f"Error getting job URL: {e}")

            # Process jobs in batches of 3
            batch_size = 2
            for i in range(0, len(job_urls), batch_size):
                batch = job_urls[i:i + batch_size]
                tasks = []
                
                for url in batch:
                    if url not in self.processed_urls:
                        tasks.append(self.process_single_job(page.context, url, processed_urls))
                
                if tasks:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in batch_results:
                        if result and not isinstance(result, Exception):
                            jobs.append(result)
                            logger.info(f"Added job: {result['title']}")
                    
                    logger.info(f"Processed batch {i//batch_size + 1}")
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

    async def search_jobs(self, title, job_location, user_id, browser_info):
        async with async_playwright() as p:
            browser = None
            try:
                # Set up browser with the provided browser info
                browser_options = {
                    'headless': True
                }         
                
                context_options = {}

                if browser_info:
                    # Configure viewport based on screen resolution
                    if browser_info.get('screen_resolution'):
                        try:
                            width, height = map(int, browser_info['screen_resolution'].split('x'))
                            context_options['viewport'] = {'width': width, 'height': height}
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"Could not parse screen resolution: {e}")
                    
                    # Set locale based on language
                    if browser_info.get('language'):
                        context_options['locale'] = browser_info['language']
                    
                    # Set timezone
                    if browser_info.get('timezone'):
                        context_options['timezone_id'] = browser_info['timezone']
                    
                    # Set user agent
                    if browser_info.get('user_agent'):
                        context_options['user_agent'] = browser_info['user_agent']
                
                browser = await p.chromium.launch(**browser_options)
                context = await browser.new_context(**context_options)

                # Log the context we're using
                logger.info(f"Browser context created with options: {context_options}")

                setup_page = await context.new_page()
                await setup_page.goto(self.base_url)
                await self.handle_cookie(setup_page)
                await setup_page.close()

                all_jobs = []

                try:
                    page = await context.new_page()
                    search_url = f"{self.base_url}/jobs/{title}/in-{job_location}?radius=30&sort=2"
                    await page.goto(search_url)
                    try:
                        await page.wait_for_selector('.res-14njlc6', timeout= 3000)
                    except Exception as selector_error:
                        logger.info(f"Selector not found, proceeding anyway: {selector_error}")
                    
                    try:
                        await page.wait_for_selector('.at-facet-header-total-results', timeout = 3000)
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
                                job_id = self.generate_job_id(job)
                                job['jobId'] = job_id

                                formatted_job = {
                                    'jobId': job_id,
                                    'title': job['title'],
                                    'company': job['company'],
                                    'location': job['location'],  
                                    'jobDescription': job['jobDescription'],  
                                    'applyLink': job['applyLink'], 
                                    'timestamp': datetime.now().isoformat(),
                                    'platform': "IrishJobs"
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
                                print(f"\nProcessing page {page_num} ({len(all_jobs)}/{self.MAX_JOBS} jobs collected)")
                                new_page = await context.new_page()
                                page_url = f"{self.base_url}/jobs/{title}/in-{job_location}?radius=20&page={page_num}&sort=2&action=sort_publish"
                                
                                try:
                                    await new_page.goto(page_url, timeout=20000)
                                    remaining_jobs = min(total_jobs - len(all_jobs), self.MAX_JOBS - len(all_jobs))
                                    if remaining_jobs > 0:
                                        page_jobs = await self.process_job_cards(new_page, self.processed_urls)
                                        for job in page_jobs[:remaining_jobs]:
                                            job_id = self.generate_job_id(job)
                                            job['jobId'] = job_id
                                            formatted_job = {
                                                'jobId': job_id,
                                                'title': job['title'],
                                                'company': job['company'],
                                                'location': job['location'],  
                                                'jobDescription': job['jobDescription'],  
                                                'applyLink': job['applyLink'], 
                                                'timestamp': datetime.now().isoformat(),
                                                'platform': "IrishJobs"
                                            }
                                            # Store in Redis
                                            self.store_job_listing(formatted_job, title, job_location)
                                            
                                            self.producer_analysis.send('analysis', value={
                                                'jobId': job_id, 
                                                'jobDescription': job['jobDescription'],
                                                'userId': user_id
                                                })
                                            self.producer_analysis.flush()

                                            self.producer_storage.send('storage', value=formatted_job)
                                            self.producer_storage.flush()
                                            all_jobs.append(formatted_job)
                                        logger.info(f"Total jobs collected: {len(all_jobs)} of {total_jobs}")
                                except Exception as page_error:
                                    print(f"Error loading page {page_num}: {page_error}")
                                finally:
                                    await new_page.close()
                                
                                page_num += 1

                            if all_jobs:
                                logger.info(f"Successfully collected and stored {len(all_jobs)} jobs")
                                return all_jobs  # Return the jobs directly
                            else:
                                logger.info("No jobs collected")
                                return []
                    except Exception as selector_error:
                        logger.info(f"Selector not found, proceeding anyway: {selector_error}")
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                    return []
            except Exception as e:
                logger.error(f"Error in search_jobs: {e}")
                return []
            finally:
                if browser:
                    await browser.close()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Flask application setup
app = Flask(__name__)
CORS(app)
scraper = IrishJobsScraper()

@app.route('/irishjobs', methods=['GET'])
def irishjobs():
    title = request.args.get('title')
    job_location = request.args.get('job_location')
    user_id = request.args.get('userId')
    
    browser_info = {
        'platform': request.args.get('platform'),
        'language': request.args.get('language'),
        'timezone': request.args.get('timezone'),
        'screen_resolution': request.args.get('screen_resolution'),
        'color_depth': request.args.get('color_depth'),
        'device_memory': request.args.get('device_memory'),
        'hardware_concurrency': request.args.get('hardware_concurrency')
    }

    logger.info(f"Request from: {request.headers.get('User-Agent')} - {request.remote_addr}")
    request_key = f"{title}:{job_location}:{user_id}"

    if not all([title, job_location, user_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    in_progress = getattr(app, '_in_progress_requests', set())

    if request_key in in_progress:
        logger.info(f"Duplicate request detected: {request_key}")
        return jsonify({"status": "pending", "message": "Request is already being processed"}), 202    
    
    # Mark this request as in progress
    in_progress.add(request_key)
    setattr(app, '_in_progress_requests', in_progress)

    try:
        cached_results = scraper.get_cached_results(title, job_location, user_id)
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
            scraped_jobs = loop.run_until_complete(scraper.search_jobs(title, job_location, user_id, browser_info))
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
        logger.error(f"Endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
    finally:
        if request_key in in_progress:
            in_progress.remove(request_key)
            setattr(app, '_in_progress_requests', in_progress)

if __name__ == "__main__":
    logger.info("Starting IrishJobs Scraper Service")
    app.run(host='0.0.0.0', port=3003, debug=True)