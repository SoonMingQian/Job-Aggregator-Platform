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

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def create_kafka_producer(retries=5):
    for attempt in range(retries):
        try:
            logger.info("Attempting to create Kafka producer (Attempt %d/%d)", attempt + 1, retries)
            return KafkaProducer(
                bootstrap_servers=['kafka1:9092', 'kafka2:9093', 'kafka3:9094'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1
            )
        except NoBrokersAvailable:
            if attempt < retries - 1:
                logger.info(f"Failed to connect to Kafka. Retrying in 5 seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(5)
            else:
                raise

# Initialize Kafka producers with retry mechanism
producerAnalysis = create_kafka_producer()
producerStorage = create_kafka_producer()

MAX_JOBS = 100

@app.route('/irishjobs', methods=['GET'])
def irishjobs():
    title = request.args.get('title')
    job_location = request.args.get('job_location')
    user_id = request.args.get('userId')
    
    logger.info("Received request - Title: %s, Location: %s, UserID: %s", 
                title, job_location, user_id)

    if not title or not job_location or not user_id:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        redis_client = init_redis()
        if not redis_client:
            return jsonify({"error": "Redis connection failed"}), 500

        # Check cache first
        cached_results = get_cached_results(redis_client, title, job_location)
        if cached_results:
            logger.info("Found %d jobs in cache", len(cached_results))
            return jsonify({
                "status": "success",
                "jobs": cached_results,
                "source": "cache"
            })

        # If no cache, run scraper
        try:
            logger.info("Cache miss - starting scraper")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the scraper and get results directly
            scraped_jobs = loop.run_until_complete(search_jobs(title, job_location, user_id))
            loop.close()

            if scraped_jobs and len(scraped_jobs) > 0:
                logger.info("Successfully scraped %d jobs", len(scraped_jobs))
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
            logger.error("Scraping error: %s", str(e))
            return jsonify({
                "status": "error",
                "error": "Scraping failed",
                "message": str(e)
            }), 500

    except Exception as e:
        logger.error("Endpoint error: %s", str(e))
        return jsonify({
            "status": "error",
            "error": "Server error",
            "message": str(e)
        }), 500
    
async def handle_cookie(page):
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

async def open_page(context, title, job_location, page_num):
    new_page = await context.new_page()
    page_url = f"https://www.irishjobs.ie/jobs/{title}/in-{job_location}?radius=30&page={page_num}&sort=2&action=sort_publish"
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
                                job_location: state.listingHeader?.listingData?.metaData?.location || 'N/A',
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
            logger.warning("Failed to extract state data")
            return None

        preloaded_state['apply_url'] = page.url
        logger.info("Extracted job: %s at %s", preloaded_state['title'], preloaded_state['company'])
        return preloaded_state

    except Exception as e:
        logger.error("Error extracting job details: %s", str(e))
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

async def search_jobs(title, job_location, user_id):
    async with async_playwright() as p:
        browser = None
        try:
            try:
                producerAnalysis.send('analysis', value={'test': 'connection'})
                producerStorage.send('storage', value={'test': 'connection'})
                producerAnalysis.flush()
                producerStorage.flush()
                logger.info("Kafka connection verified")
            except Exception as e:
                logger.error(f"Kafka connection failed: {e}")
                return []
            
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            all_jobs = []
            processed_urls = set()

            # Initialize Redis Connection
            redis_client = init_redis()
            if not redis_client:
                logger.error("Failed to connect to Redis")
                return []  # Return empty list instead of None

            try:
                page = await context.new_page()
                search_url = f"https://www.irishjobs.ie/jobs/{title}/in-{job_location}?radius=30&sort=2&action=sort_publish"
                await page.goto(search_url)
                await handle_cookie(page)
                await page.wait_for_selector('.res-14njlc6')

                # Get total jobs count first
                total_jobs_element = await page.query_selector('.at-facet-header-total-results')
                if total_jobs_element:
                    total_jobs_text = await total_jobs_element.inner_text()
                    total_jobs = min(int(total_jobs_text.split()[0]), MAX_JOBS)  # Limit to MAX_JOBS
                    print(f"\nNeed to collect {total_jobs} total jobs (limited to {MAX_JOBS} maximum)")
                    
                    # Calculate required pages (25 jobs per page)
                    required_pages = min((total_jobs + 24) // 25, (MAX_JOBS + 24) // 25)  # Limit pages based on MAX_JOBS
                    print(f"Will process up to {required_pages} pages")

                    # Process first page
                    first_page_jobs = await process_job_cards(page, processed_urls)
                    # Only take up to total_jobs or MAX_JOBS from first page
                    for job in first_page_jobs[:min(total_jobs, MAX_JOBS)]:
                        job_id = generate_job_id(job)
                        job['jobId'] = job_id
                        all_jobs.append(job)
                        # Store in Redis
                        store_job_listing(redis_client, job, title, job_location)
                        producerAnalysis.send('analysis', value={
                            'jobId': job_id, 
                            'jobDescription': job['description'],
                            'userId': user_id
                            })
                        producerAnalysis.flush()

                        producerStorage.send('storage', value=job)
                        producerStorage.flush()
                    jobs_collected = len(all_jobs)
                    jobs_collected = len(all_jobs)
                    print(f"Collected {jobs_collected} jobs from page 1")

                    # Process additional pages if needed and haven't reached MAX_JOBS
                    page_num = 2
                    while len(all_jobs) < total_jobs and len(all_jobs) < MAX_JOBS and page_num <= required_pages:
                        print(f"\nProcessing page {page_num} ({len(all_jobs)}/{MAX_JOBS} jobs collected)")
                        new_page = await context.new_page()
                        page_url = f"https://www.irishjobs.ie/jobs/{title}/in-{job_location}?radius=30&page={page_num}&sort=2&action=sort_publish"
                        
                        try:
                            await new_page.goto(page_url, timeout=20000)
                            remaining_jobs = min(total_jobs - len(all_jobs), MAX_JOBS - len(all_jobs))
                            if remaining_jobs > 0:
                                page_jobs = await process_job_cards(new_page, processed_urls)
                                for job in page_jobs[:remaining_jobs]:
                                    job_id = generate_job_id(job)
                                    job['jobId'] = job_id
                                    all_jobs.append(job)
                                    # Store in Redis
                                    store_job_listing(redis_client, job, title, job_location)
                                    producerAnalysis.send('analysis', value={
                                        'jobId': job_id, 
                                        'jobDescription': job['description'],
                                        'userId': user_id
                                        })
                                    producerAnalysis.flush()

                                    producerStorage.send('storage', value=job)
                                    producerStorage.flush()
                                print(f"Total jobs collected: {len(all_jobs)} of {total_jobs}")
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

            except Exception as e:
                logger.error(f"Error occurred: {e}")
                return []
        except Exception as e:
            logger.error(f"Error in search_jobs: {str(e)}")
            return []
        finally:
            if browser:
                await browser.close()

"""Redis"""
def init_redis():
    try:
        logger.info("Initializing Redis connection")
        redis_client = Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis connection successful")
        return redis_client
    except Exception as e:
        logger.error("Failed to connect to Redis: %s", str(e))
        return None

def generate_job_id(job_data):
    unique_string = f"{job_data['company']}:{job_data['title']}:{job_data['job_location']}:{job_data['posted_date']}"
    job_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
    return f"job:{job_id}"

def generate_cache_key(title, job_location):
    return f"search:{title.lower()}:{job_location.lower()}:irishJobs"

def get_cached_results(redis_client, title, job_location):
    cache_key = generate_cache_key(title, job_location)
    cached_jobs = redis_client.smembers(cache_key)

    if cached_jobs:
        jobs = []
        for job_key in cached_jobs:
            job_data = redis_client.hgetall(job_key)
            jobs.append(job_data)
        print(jobs)
        return jobs
    return None

def store_job_listing(redis_client, job_data, title, job_location):
    try:
        job_key = job_data['jobId']
        redis_client.hmset(job_key, job_data)
        cache_key = generate_cache_key(title, job_location)
        redis_client.sadd(cache_key, job_key)
        redis_client.expire(job_key, 86400)  # Expire in 24 hours
        redis_client.expire(cache_key, 86400)  # Expire in 24 hours
        return job_key
    except Exception as e:
        print(f"Error while storing job listing: {e}")
        return None
    

# Remove global producer initialization
# producerAnalysis = create_kafka_producer()
# producerStorage = create_kafka_producer()

# Add producer initialization in the app
def initialize_kafka():
    global producerAnalysis, producerStorage
    logger.info("Initializing Kafka producers...")
    producerAnalysis = create_kafka_producer()
    producerStorage = create_kafka_producer()
    logger.info("Kafka producers initialized successfully")

# Modify the main function to initialize Kafka before starting the app
if __name__ == "__main__":
    logger.info("Starting IrishJobs Scraper Service")
    try:
        initialize_kafka()
        logger.info("Starting server on port 3003")
        app.run(
            host='0.0.0.0', 
            debug=True, 
            port=3003,
            threaded=True,
            # Increase timeout for long-running scrapes
            request_timeout=300
        )
    except Exception as e:
        logger.error(f"Failed to start service: {e}")