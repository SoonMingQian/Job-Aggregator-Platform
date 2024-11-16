from playwright.sync_api import sync_playwright
from redis import Redis
from datetime import datetime
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/jobie', methods=['GET'])
def jobie():
    job_title = request.args.get('job_title')
    job_location = request.args.get('job_location')

    if not job_title or not job_location:
        return jsonify({"error": "Missing job_title or job_location parameter"}), 400

    # Run the job search
    results = run(job_title, job_location)
    
    return jsonify(results)

def run(job_title, job_location):
    redis_client = init_redis()

    cached_results = get_cached_results(redis_client, job_title, job_location)
    if cached_results:
        print("Using cached results")
        return cached_results

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.jobs.ie/")
        search_jobs(redis_client, page, browser, job_title, job_location)

def search_jobs(redis_client, page, browser, job_title, job_location):
    cookies(page)
    # Search for jobs
    page.wait_for_selector('#stepstone-autocomplete-150')
    page.locator('#stepstone-autocomplete-150').fill(job_title)
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
    
        # Get job details
        for job in range(count):
            job_listing = job_listings.nth(job)
            job_data = {
                'job_title': job_listing.locator('a[data-testid="job-item-title"] .res-nehv70').text_content(),
                'apply_link': job_listing.locator('a[data-testid="job-item-title"]').get_attribute('href'),
                'company': job_listing.locator('span[data-at="job-item-company-name"]').text_content(),
                'location': job_listing.locator('span[data-at="job-item-location"]').text_content(),
                'content': job_listing.locator('div[data-at="jobcard-content"]').text_content(),
                'timestamp': datetime.now().isoformat()
            }

            print(job_data)

            store_job_listing(redis_client, job_data, job_title, job_location)
        
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
            host='localhost',
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
    unique_string = f"{job_data['company']}:{job_data['job_title']}:{job_data['location']}"
    # Generate UUID based on the unique string
    job_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
    return f"job:{job_id}"

def generate_cache_key(job_title, job_location):
    # Result: "search:part time:dublin"
    return f"search:{job_title.lower()}:{job_location.lower()}"

def get_cached_results(redis_client, job_title, job_location):
    cache_key = generate_cache_key(job_title, job_location)
    # smembers returns a set of all the values in the set
    cached_jobs = redis_client.smembers(cache_key)

    if cached_jobs:
        jobs = []
        for job_key in cached_jobs:
            job_data = redis_client.hgetall(job_key)
            if job_data:
                jobs.append(job_data)
        print(jobs)
        return jobs
    return None

def store_job_listing(redis_client, job_data, job_title, job_location):
    try:
        # Generate unique job key
        job_key = generate_job_id(job_data)

        redis_client.hmset(job_key, job_data)

        cache_key = generate_cache_key(job_title, job_location)
        redis_client.sadd(cache_key, job_key)

        redis_client.expire(job_key, 86400)  # Expire in 24 hours
        redis_client.expire(cache_key, 86400)  # Expire in 24 hours

        return job_key
    except Exception as e:
        print(f"Error while storing job listing: {e}")
        return None

def close(browser):
    browser.close()
