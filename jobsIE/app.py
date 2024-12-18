from playwright.sync_api import sync_playwright
from redis import Redis
from datetime import datetime
import uuid
from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json
import os

import time
from kafka.errors import NoBrokersAvailable

app = Flask(__name__)

def create_kafka_producer(retries=5):
    for attempt in range(retries):
        try:
            return KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except NoBrokersAvailable:
            if attempt < retries - 1:
                print(f"Failed to connect to Kafka. Retrying in 5 seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(5)
            else:
                raise

# Initialize Kafka producers with retry mechanism
producerAnalysis = create_kafka_producer()
producerStorage = create_kafka_producer()

@app.route('/jobie', methods=['GET'])
def jobie():
    title = request.args.get('title')
    job_location = request.args.get('job_location')

    if not title or not job_location:
        return jsonify({"error": "Missing title or job_location parameter"}), 400

    # Run the job search
    results = run(title, job_location)
    
    return jsonify(results)

def run(title, job_location):
    redis_client = init_redis()

    cached_results = get_cached_results(redis_client, title, job_location)
    if cached_results:
        print("Using cached results")
        return cached_results

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()
        page.goto("https://www.jobs.ie/")
        search_jobs(redis_client, page, browser, title, job_location)

def search_jobs(redis_client, page, browser, title, job_location):
    cookies(page)
    # Search for jobs
    page.wait_for_selector('#stepstone-autocomplete-150')
    page.locator('#stepstone-autocomplete-150').fill(title)
    page.locator('#stepstone-autocomplete-155').fill(job_location)
    page.locator('button.sbr-18wqljt').click()

    # Get the number of pages
    number_of_pages = get_number_of_pages(page)
    print(number_of_pages)
    for page_number in range(1, number_of_pages + 1):
        # Get the number of job listings
        job_listings = page.locator('article.res-ezkvph')
        page.wait_for_selector('article.res-ezkvph')
        count = job_listings.count()
        print(count)

        page.wait_for_selector('a[data-testid="job-item-title"]') 
        page.wait_for_selector('span[data-at="job-item-company-name"]')
        page.wait_for_selector('span[data-at="job-item-location"]')
        page.wait_for_selector('div[data-at="jobcard-content"]')  
       
        # Get job details
        for job in range(count):
            job_listing = job_listings.nth(job)
            job_data = {
                'title': job_listing.locator('a[data-testid="job-item-title"] .res-nehv70').text_content(),
                'applyLink': "https://www.jobs.ie/" + job_listing.locator('a[data-testid="job-item-title"]').get_attribute('href'),
                'company': job_listing.locator('span[data-at="job-item-company-name"]').text_content(),
                'location': job_listing.locator('span[data-at="job-item-location"]').text_content(),
                'jobDescription': " ".join([el.text_content() for el in job_listing.locator('div[data-at="jobcard-content"]').all()]),
                'timestamp': datetime.now().isoformat()
            }

            job_id = generate_job_id(job_data)
            job_data['jobId'] = job_id
            
            print(job_data)

            store_job_listing(redis_client, job_data, title, job_location)
            producerAnalysis.send('analysis', value={'jobId': job_id, 'jobDescription': job_data['jobDescription']})
            producerAnalysis.flush()

            producerStorage.send('storage', value=job_data)
            producerStorage.flush()

        print(f"Page {page_number} done")
            
        if page_number < number_of_pages:
            try:
                next_button = page.locator('a[aria-label="Next"]')
                next_button.click()
            except Exception as e:
                print(f"Error while clicking the next button: {e}")
                break

    close(browser)

def get_number_of_pages(page):
    try:
        page.wait_for_selector('nav[aria-label="pagination"] span[role="status"]', timeout=3000)
        pagination_text = page.locator('nav[aria-label="pagination"] span[role="status"]').text_content()
        # Extract the number of pages from the text "Page X of Y"
        number_of_pages = int(pagination_text.split()[-1])
        return number_of_pages
    except Exception as e:
        print(f"Error while getting the number of pages: {e}")
        return 0

def cookies(page):
    try:
        page.wait_for_selector('#ccmgt_explicit_accept', timeout=1500)
        page.locator('#ccmgt_explicit_accept').click()
    except Exception as e:
        print(f"Button not found or not clickable: {e}")

""" Redis functions """
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
    # Create unique identifier using company name and job title
    unique_string = f"{job_data['company']}:{job_data['title']}:{job_data['location']}"
    # Generate UUID based on the unique string
    job_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
    return f"job:{job_id}"

def generate_cache_key(title, job_location):
    # Result: "search:part time:dublin"
    return f"search:{title.lower()}:{job_location.lower()}:jobsIE"

def get_cached_results(redis_client, title, job_location):
    cache_key = generate_cache_key(title, job_location)
    # smembers returns a set of all the values in the set
    cached_jobs = redis_client.smembers(cache_key)

    if cached_jobs:
        jobs = []
        for job_key in cached_jobs:
            job_data = redis_client.hgetall(job_key)
            if job_data:
                #Get skills from this job
                skills_key = f"job:{job_key}:skills"
                skills = redis_client.smembers(skills_key)
                job_data['skills'] = list(skills) if skills else []
                jobs.append(job_data)
        print(jobs)
        return jobs
    return None

def store_job_listing(redis_client, job_data, title, job_location):
    try:
        # Generate unique job key
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

def close(browser):
    browser.close()

if __name__ == '__main__':
   # Set Flask environment variables
    os.environ['FLASK_DEBUG'] = '1'  # Replace FLASK_ENV
    os.environ['FLASK_APP'] = 'app.py'
    app.run(host='0.0.0.0', debug=True, port=3002)