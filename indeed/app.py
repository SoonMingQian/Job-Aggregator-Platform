import asyncio
from playwright.async_api import async_playwright
from flask import Flask, request, jsonify
import redis.asyncio as redis
from datetime import datetime
from kafka import KafkaProducer
import json
import os
import logging
import time
from kafka.errors import NoBrokersAvailable
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_kafka_producer(retries=5):
    for attempt in range(retries):
        try:
            return KafkaProducer(
                bootstrap_servers=['kafka1:9092', 'kafka2:9093', 'kafka3:9094'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1
            )
        except NoBrokersAvailable:
            if attempt < retries - 1:
                logger.error(f"Failed to connect to Kafka. Retrying in 5 seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(5)
            else:
                raise

# Initialize Kafka producers with retry mechanism
producerAnalysis = create_kafka_producer()
producerStorage = create_kafka_producer()

@app.route('/indeed', methods=['GET'])
def indeed():
    job_title = request.args.get('job_title')
    job_location = request.args.get('job_location')
    user_agent = request.args.get('user_agent')
    user_id = request.args.get('userId') 
    # Get client IP considering Docker networking
    client_ip = request.headers.get('X-Real-IP', request.remote_addr)
    
    # If we're getting Docker's internal IP, try other headers
    if client_ip.startswith('172.') or client_ip.startswith('192.168.'):
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        # Get first IP if multiple are present
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
    browser_info = {
        'platform': request.args.get('platform'),
        'language': request.args.get('language'),
        'timezone': request.args.get('timezone'),
        'screen_resolution': request.args.get('screen_resolution'),
        'color_depth': request.args.get('color_depth'),
        'device_memory': request.args.get('device_memory'),
        'hardware_concurrency': request.args.get('hardware_concurrency')
    }

    if not job_title or not job_location or not user_id:
        logger.error("Missing parameters")
        return jsonify({"error": "Missing job_title or job_location parameter"}), 400

    # Run the job search
    results = asyncio.run(main(job_title, job_location, user_agent, client_ip, browser_info, user_id))
    logger.info(f"Scraping completed. Found {len(results) if results else 0} jobs")
    return jsonify(results)

async def check_pages(job_title, job_location, context, browser_info): 
    page = await context.new_page()

    try:
        # Add browser fingerprint data right after creating the page
        await page.evaluate(f'''
            Object.defineProperty(navigator, 'platform', {{ get: () => '{browser_info["platform"]}' }});
            Object.defineProperty(navigator, 'language', {{ get: () => '{browser_info["language"]}' }});
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {browser_info["device_memory"]} }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {browser_info["hardware_concurrency"]} }});
        ''')

        # Intercept and handle redirects
        async def handle_route(route):
            if 'start=0' in route.request.url:
                # Block redirect to start=0
                await route.abort()
            else:
                await route.continue_()
                
        await page.route('**/*', handle_route)
        
        # Initial delay
        await page.wait_for_timeout(random.randint(2000, 4000))
        
        # Start with page 1000
        url = f"https://ie.indeed.com/jobs?q={job_title}&l={job_location}&start=1000"
        response = await page.goto(url, wait_until='networkidle', timeout=30000)


        # Ensure page loads completely
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        
        # Get pagination info
        pagination = await page.wait_for_selector('ul.css-z64vyd.eu4oa1w0', timeout=10000)
        if pagination:
            pagination_links = page.locator('ul.css-z64vyd.eu4oa1w0 > li > a')
            count = await pagination_links.count()
            last_page_text = await pagination_links.nth(count - 1).text_content()
            return int(last_page_text)
        
        return 10
    except Exception as e:
        logger.error(f"Error in check_pages: {e}")
        return 10
    finally:
        await page.close()

async def get_jobs(redis_client, page, job_title, job_location, user_id):
    jobs = []
    try:
        # Wait for job cards with timeout
        try:
            await page.wait_for_selector('a.jcs-JobTitle', timeout=10000)
            job_links = page.locator('a.jcs-JobTitle')
            count = await job_links.count()
            logger.info(f"Found {count} jobs")
        except Exception as e:
            logger.error(f"Timeout waiting for job cards: {e}")
            return jobs
        
        for i in range(count):
            try:
                job_link = job_links.nth(i)

                # title:
                try:
                    title = await job_link.inner_text(timeout=5000)
                    title = title.strip() if title else "N/A"
                except Exception:
                    title = "N/A"
                    logger.error(f"Timeout getting job title for job {i}") 

                # Next Job
                try:
                    await job_link.click(timeout=5000)
                    await page.wait_for_timeout(1000)
                except Exception as e:
                    logger.error(f"Timeout clicking job link: {e}")
                    continue

                # Job Id
                try:
                    job_id = await job_link.get_attribute('data-jk', timeout=5000)
                except Exception:
                    job_id = "N/A"
                    logger.error(f"Timeout getting job ID for job {i}")

                # Apply Link
                apply_link = None
                try:
                    # Try first type - apply button
                    apply_button = page.locator('button[aria-haspopup="dialog"][buttontype="primary"]')
                    await apply_button.wait_for(timeout=3000)
                    if await apply_button.count() > 0:
                        href = await apply_button.get_attribute('href')
                        logger.info(f"Found apply button href: {href}")
                        if href:
                            apply_link = href if href.startswith('https://ie.indeed.com') else f"https://ie.indeed.com{href}"
                    
                    # If first type fails, try second type
                    if not apply_link:
                        indeed_button = page.locator('#indeedApplyButton')
                        await indeed_button.wait_for(timeout=3000)
                        if await indeed_button.count() > 0:
                            wrapper = page.locator('.jobsearch-IndeedApplyButton-contentWrapper')
                            href = await wrapper.evaluate('''(el) => {
                                const link = el.closest('a');
                                return link ? link.href : null;
                            }''', timeout=3000)
                            logger.info(f"Found indeed button href: {href}")
                            if href:
                                apply_link = href if href.startswith('https://ie.indeed.com') else f"https://ie.indeed.com{href}"
                    
                    # Fallback to job view URL
                    if not apply_link:
                        apply_link = f"https://ie.indeed.com/viewjob?jk={job_id}"
                        logger.info(f"Using fallback URL: {apply_link}")
                        
                except Exception as e:
                    logger.error(f"Error getting apply link: {e}")
                    apply_link = f"https://ie.indeed.com/viewjob?jk={job_id}"

                # Company
                company = "N/A"
                for selector in [
                    '.jobsearch-JobInfoHeader-companyNameSimple',
                    '.jobsearch-JobInfoHeader-companyNameLink',
                    "[data-testid='inlineHeader-companyName']"
                ]:
                    try:
                        company_element = page.locator(selector)
                        await company_element.wait_for(timeout=3000)
                        if await company_element.count() > 0:
                            company = await company_element.inner_text(timeout=3000)
                            break
                    except Exception:
                        continue

                # Location
                try:
                    location_element = page.locator("[data-testid='jobsearch-JobInfoHeader-companyLocation']").first
                    await location_element.wait_for(timeout=3000)
                    location = await location_element.inner_text(timeout=3000)
                except Exception:
                    location = "N/A"
                    logger.error(f"Timeout getting location for job {i}")

                # Job Description
                try:
                    desc_element = page.locator("#jobDescriptionText")
                    await desc_element.wait_for(timeout=5000)
                    job_desc = await desc_element.inner_text(timeout=5000)
                except Exception:
                    job_desc = "N/A"
                    logger.error(f"Timeout getting job description for job {i}")

                job_data = {
                    'jobId': job_id,
                    'title': title,
                    'company': company.strip(),
                    'location': location.strip(),
                    'apply_link': apply_link or "N/A",
                    'jobDescription': job_desc.strip()
                }

                jobs.append(job_data)

                await store_job_listing(redis_client, job_data, job_title, job_location)
                await process_job(job_data, user_id)
                logger.info(f"Processed job {i}: {job_data}")
                
            except Exception as e:
                logger.error(f"Error processing job {i}: {e}")
                continue

        return jobs
        
    except Exception as e:
        logger.error(f"Error in get_jobs: {e}")
        return jobs

async def process_job(job_data, user_id):
    try:
        job_id = job_data['jobId']
        job_description = job_data['jobDescription']
        logger.info(f"Processing job ID: {job_id} for user: {user_id}")
        kafka_message = {
            'jobId': job_id,
            'jobDescription': job_description,
            'userId': user_id,  # Add userId to message
            'timestamp': datetime.now().isoformat()
        }
        producerAnalysis.send('analysis', value=kafka_message)
        producerAnalysis.flush()
        logger.info(f"Successfully sent job {job_id} to Kafka")
    except Exception as e:
        logger.error(f"Error in process_job: {e}")
        raise

async def scrape_job_data(job_title, job_location, start, context, browser_info, user_id):
    page = await context.new_page()
    try:
        # Add browser fingerprint data right after creating the page
        await page.evaluate(f'''
            Object.defineProperty(navigator, 'platform', {{ get: () => '{browser_info["platform"]}' }});
            Object.defineProperty(navigator, 'language', {{ get: () => '{browser_info["language"]}' }});
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {browser_info["device_memory"]} }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {browser_info["hardware_concurrency"]} }});
        ''')

        # Random delay before loading page
        await page.wait_for_timeout(random.randint(2000, 5000))
        
        url = f"https://ie.indeed.com/jobs?q={job_title}&l={job_location}&start={start}"
        await page.goto(url, wait_until='networkidle')

        # Simulate human scrolling
        for _ in range(3):
            await page.mouse.wheel(0, random.randint(100, 300))
            await page.wait_for_timeout(random.randint(500, 1500))
        
        # Random mouse movements
        for _ in range(2):
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
            await page.wait_for_timeout(random.randint(500, 1000))
        
        redis_client = await init_redis()  # Get redis client
        jobs = await get_jobs(redis_client, page, job_title, job_location, user_id)  # Pass redis_client
        return jobs
    finally:
        await page.close()
    
async def main(job_title, job_location, user_agent, client_ip, browser_info, user_id):
    redis_client = await init_redis()
    cached_results = await get_cached_results(redis_client, job_title, job_location)
    if cached_results:
        logger.info("Using cached results")
        return cached_results
    
    jobs_list = []
    try:
        async with async_playwright() as playwright:
            # Launch browser with user's configuration
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    f'--window-size={browser_info["screen_resolution"]}',
                    f'--device-memory={browser_info["device_memory"]}',
                    f'--cpu-count={browser_info["hardware_concurrency"]}',
                ]
            )

            # Create context with user's data - removed client_ip
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={
                    'width': int(browser_info["screen_resolution"].split('x')[0]),
                    'height': int(browser_info["screen_resolution"].split('x')[1])
                },
                locale=browser_info["language"],
                timezone_id=browser_info["timezone"],
                color_scheme=browser_info.get("color_scheme", "light"),
                reduced_motion="reduce",
                extra_http_headers={
                    'Accept-Language': f'{browser_info["language"]},en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'X-Forwarded-For': client_ip  # Add client IP as header instead
                }
            )
    
            try:
                # Get total pages using the same context
                last_page_number = await check_pages(job_title, job_location, context, browser_info)
                logger.info(f"Found {last_page_number} pages")

                if last_page_number == 1:
                    page_jobs = await scrape_job_data(job_title, job_location, 0, context, browser_info, user_id)
                    jobs_list.extend(page_jobs)
                else:
                    tasks = []
                    for start in range(0, last_page_number * 10, 10):
                        task = asyncio.create_task(
                            scrape_job_data(job_title, job_location, start, context, browser_info, user_id)
                        )
                        tasks.append(task)
                    results = await asyncio.gather(*tasks)
                    for page_jobs in results:
                        jobs_list.extend(page_jobs)

            finally:
                # Stop tracing and save
                await context.close()
                await browser.close()
        
            return jobs_list
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return {
            "status": "error",
            "message": str(e),
            "jobs": []
        }


"""Redis functions"""
async def init_redis():
    try:
        redis_client = await redis.from_url('redis://redis:6379', encoding='utf-8', decode_responses=True)
        return redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None

async def generate_cache_key(job_title, job_location):
    logger.info(f"Generating cache key for Job Title: {job_title}, Job Location: {job_location}")
    return f"search:{job_title.lower()}:{job_location.lower()}:indeed"

async def get_cached_results(redis_client, job_title, job_location):
    try:
        cache_key = await generate_cache_key(job_title, job_location)
        logger.info(f"Cache Key: {cache_key}")
        cached_jobs = await redis_client.smembers(cache_key)

        if cached_jobs:
            jobs = []
            for job_key in cached_jobs:
                job_data = await redis_client.hgetall(job_key)
                if job_data:
                    # Get skills from this job
                    skills_key = f"job:{job_key}:skills"
                    skills = await redis_client.smembers(skills_key)
                    job_data['skills'] = list(skills) if skills else []
                    jobs.append(job_data)
            logger.info(jobs)
            return jobs
        return None
    except Exception as e:
        logger.error(f"Error getting cached results: {e}")
        return None

async def store_job_listing(redis_client, job_data, job_title, job_location):
    try:
        job_key = f"job:{job_data['jobId']}"
        await redis_client.hmset(job_key, job_data)
        cache_key = await generate_cache_key(job_title, job_location)
        logger.info(f"Storing job with key: {job_key} in cache key: {cache_key}")
        await redis_client.sadd(cache_key, job_key)

        await redis_client.expire(job_key, 86400)  # Expire in 24 hours
        await redis_client.expire(cache_key, 86400)  # Expire in 24 hours

        return job_key
    except Exception as e:
        logger.error(f"Error while storing job listing: {e}")
        return None
    
if __name__ == '__main__':
    os.environ['FLASK_DEBUG'] = '1'  # Replace FLASK_ENV
    os.environ['FLASK_APP'] = 'app.py'
    app.run(host='0.0.0.0', debug=True, port=3001)  # Indeed scraper port