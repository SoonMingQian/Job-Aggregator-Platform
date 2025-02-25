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
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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

    async def handle_cookie(self, page):
        try:
            accept_button = await page.wait_for_selector('#ccmgt_explicit_accept', timeout=5000)
            if accept_button:
                await accept_button.click()
                await page.wait_for_selector('#ccmgt_explicit_accept', state='hidden', timeout=5000)
                logger.info("Cookie accepted")
        except Exception as e:
            logger.warning(f"Cookie handling error: {e}")

    async def extract_job_details(self, page):
        try:
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

    async def process_job_cards(self, page):
        jobs = []
        try:
            await page.wait_for_selector('article.res-1p8f8en')
            job_cards = await page.query_selector_all('article.res-1p8f8en')
            
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

            batch_size = 3
            for i in range(0, len(job_urls), batch_size):
                batch = job_urls[i:i + batch_size]
                tasks = []
                
                for url in batch:
                    if url not in self.processed_urls:
                        tasks.append(self.process_single_job(page.context, url))
                
                if tasks:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in batch_results:
                        if result and not isinstance(result, Exception):
                            jobs.append(result)
                            logger.info(f"Added job: {result['title']}")
                    
                    logger.info(f"Processed batch {i//batch_size + 1}")
                    await asyncio.sleep(1)

            return jobs

        except Exception as e:
            logger.error(f"Error processing page: {e}")
            return []

    async def process_single_job(self, context, url):
        job_page = None
        try:
            job_page = await context.new_page()
            await job_page.goto(url, timeout=15000, wait_until='commit')
            
            job_data = await asyncio.wait_for(
                self.extract_job_details(job_page),
                timeout=10.0
            )
            
            if job_data:
                self.processed_urls.add(url)
                return job_data
                
        except Exception as e:
            logger.error(f"Error processing job {url}: {e}")
            return None
        finally:
            if job_page:
                await job_page.close()

    def generate_job_id(self, job_data):
        unique_string = f"{job_data['company']}:{job_data['title']}:{job_data['location']}:{job_data['posted_date']}"
        job_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
        return f"job:{job_id}"

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

    async def search_jobs(self, title, job_location, user_id):
        async with async_playwright() as p:
            browser = None
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                search_url = f"{self.base_url}/jobs/{title}/in-{job_location}?radius=30&sort=2"
                await page.goto(search_url)
                await self.handle_cookie(page)

                jobs = await self.process_job_cards(page)
                processed_jobs = []

                for job in jobs[:self.MAX_JOBS]:
                    job_id = self.generate_job_id(job)
                    formatted_job = {
                        'jobId': job_id,
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location'],  # Already correct from extract_job_details
                        'jobDescription': job['jobDescription'],  # Already correct from extract_job_details
                        'applyLink': job['applyLink'],  # Already correct from extract_job_details
                        'timestamp': datetime.now().isoformat(),
                    }
                    
                    if self.redis_client:
                        self.store_job_listing(formatted_job, title, job_location)
                    
                    if self.producer_analysis and self.producer_storage:
                        self.producer_analysis.send('analysis', value={
                            'jobId': job_id,
                            'jobDescription': formatted_job['jobDescription'],  # Changed from description
                            'userId': user_id
                        })
                        logger.info(f"Sending to storage with fields: {formatted_job.keys()}")
                        self.producer_storage.send('storage', value=formatted_job)
                    
                    processed_jobs.append(formatted_job)  # Changed from job to formatted_job

                if self.producer_analysis:
                    self.producer_analysis.flush()
                if self.producer_storage:
                    self.producer_storage.flush()

                return processed_jobs

            except Exception as e:
                logger.error(f"Error in search_jobs: {e}")
                return []
            finally:
                if browser:
                    await browser.close()

# Flask application setup
app = Flask(__name__)
CORS(app)
scraper = IrishJobsScraper()

@app.route('/irishjobs', methods=['GET'])
def irishjobs():
    title = request.args.get('title')
    job_location = request.args.get('job_location')
    user_id = request.args.get('userId')
    
    if not all([title, job_location, user_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        jobs = loop.run_until_complete(scraper.search_jobs(title, job_location, user_id))
        loop.close()

        if jobs:
            return jsonify({
                "status": "success",
                "jobs": jobs,
                "total": len(jobs)
            })
        
        return jsonify({
            "status": "success",
            "jobs": [],
            "message": "No jobs found"
        })

    except Exception as e:
        logger.error(f"Endpoint error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    logger.info("Starting IrishJobs Scraper Service")
    app.run(host='0.0.0.0', port=3003, debug=True)