import asyncio
from playwright.async_api import async_playwright
from flask import Flask, request, jsonify
import redis.asyncio as redis
from datetime import datetime
from kafka import KafkaProducer
import json
import os

app = Flask(__name__)

# Iniitialize Kafka producer
producerAnalysis = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

producerStorage = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/indeed', methods=['GET'])
def indeed():
    job_title = request.args.get('job_title')
    job_location = request.args.get('job_location')

    if not job_title or not job_location:
        return jsonify({"error": "Missing job_title or job_location parameter"}), 400

    # Run the job search
    results = asyncio.run(main(job_title, job_location))
    print("Done Scraping")
    return jsonify(results)

async def check_pages(job_title, job_location, browser):
    context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    page = await context.new_page()
    url = f"https://ie.indeed.com/jobs?q={job_title}&l={job_location}&start=1000"
    await page.goto(url)
    
    try:
        await page.wait_for_selector('ul.css-1g90gv6.eu4oa1w0', timeout=3000)
        pagination_links = page.locator('ul.css-1g90gv6.eu4oa1w0 > li > a')
        count = await pagination_links.count()
        last_page_text = await pagination_links.nth(count - 1).text_content()
        print(f"Last page number: {last_page_text}")
        return int(last_page_text)
    except Exception as e:
        print(f"Pagination links not found: {e}")
        return 1
    finally:
        await page.close()
        await context.close()

async def get_jobs(redis_client, page, job_title, job_location):
    try:
        await page.wait_for_selector('a.jcs-JobTitle')
        job_links = page.locator('a.jcs-JobTitle')
        count = await job_links.count()
        print(f"Generating cache key in get_jobs: {job_title}, Job Location: {job_location}")
        for job in range(count):
            job_link = job_links.nth(job)
            await job_link.click()
            await page.wait_for_selector('div.jobsearch-ViewJobLayout--embedded') 
            
            
            title = await page.locator('h2.jobsearch-JobInfoHeader-title').text_content()
            company = await page.locator('a.css-1ioi40n.e19afand0').text_content()
            if '.c' in company:
                company = company.split('.c')[0]
            # company_link = await page.locator('a.css-1ioi40n.e19afand0').get_attribute('href')
            location_div = await page.locator('div[data-testid="inlineHeader-companyLocation"] > div').text_content()
            
            location_parts = location_div.split('•')
            location = location_parts[0].strip()
            # work_mode = location_parts[1].strip() if len(location_parts) > 1 else 'N/A'
            
            job_id = await job_link.get_attribute('data-jk')

            job_description_element = page.locator('div#jobDescriptionText')
            job_description = ""
            if await job_description_element.count() > 0:
                paragraphs = job_description_element.locator('p')
                lists = job_description_element.locator('ul')
                for i in range(await paragraphs.count()):
                    job_description += await paragraphs.nth(i).inner_text()
                for i in range(await lists.count()):
                    job_description += await lists.nth(i).inner_text()
            else:
                job_description = "N/A"
            
            try:
                apply_link = await page.locator('button.css-1234qe1.e8ju0x51').get_attribute('href', timeout=100)
            except:
                apply_link = f'https://ie.indeed.com/viewjob?jk={job_id}'          
            
            job_data = {
                'jobId': job_id,
                'title': title,
                'company': company,
                # 'company_link': company_link,
                'location': location,
                # 'work_mode': work_mode,
                'applyLink': apply_link,
                'jobDescription': job_description,
                'timestamp': datetime.now().isoformat()
            }

            print(job_data)
            await store_job_listing(redis_client, job_data, job_title, job_location)
            await process_job(job_data)
            print("--------------------------job done---------------------------")
    except Exception as e:
        print(f"Error in get_jobs: {e}")

async def process_job(job_data):
    try:
        job_id = job_data['jobId']
        job_description = job_data['jobDescription']
        print(f"Processing job ID: {job_id}")
        producerAnalysis.send('analysis', value={
            'jobId': job_id, 
            'jobDescription': job_description
        })
        producerAnalysis.flush()
        print(f"Successfully sent job {job_id} to Kafka")
    except Exception as e:
        print(f"Error in process_job: {e}")
        raise

async def scrape_job_data(redis_client, job_title, job_location, start, browser):
    context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    page = await context.new_page()
    url = f"https://ie.indeed.com/jobs?q={job_title}&l={job_location}&start={start}"
    await page.goto(url)
    print(f"Generating cache key in scrape_job_data: {job_title}, Job Location: {job_location}")
    await get_jobs(redis_client, page, job_title, job_location)
    await page.close()
    await context.close()
    
async def main(job_title, job_location):
    redis_client = await init_redis()
    cached_results = await get_cached_results(redis_client, job_title, job_location)
    if cached_results:
        print("Using cached results")
        return cached_results
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']  # Disable headless detection
        )
        
        last_page_number = await check_pages(job_title, job_location, browser)
        
        if last_page_number == 1:
            await scrape_job_data(redis_client, job_title, job_location, 0, browser)
        else:
            tasks = []
            for start in range(0, last_page_number * 10, 10):
                task = asyncio.create_task(scrape_job_data(redis_client, job_title, job_location, start, browser))
                tasks.append(task)
            await asyncio.gather(*tasks)
        
        await browser.close()

def close_browser(browser):
    print('No page anymore')
    while True:
        continue
    browser.close()

"""Redis functions"""
async def init_redis():
    try:
        redis_client = await redis.from_url('redis://localhost:6379', encoding='utf-8', decode_responses=True)
        return redis_client
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return None

async def generate_cache_key(job_title, job_location):
    print(f"Generating cache key for Job Title: {job_title}, Job Location: {job_location}")
    return f"search:{job_title.lower()}:{job_location.lower()}:indeed"

async def get_cached_results(redis_client, job_title, job_location):
    try:
        cache_key = await generate_cache_key(job_title, job_location)
        print(f"Cache Key: {cache_key}")
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
            print(jobs)
            return jobs
        return None
    except Exception as e:
        print(f"Error getting cached results: {e}")
        return None

async def store_job_listing(redis_client, job_data, job_title, job_location):
    try:
        job_key = job_data['jobId']
        await redis_client.hmset(job_key, job_data)
        cache_key = await generate_cache_key(job_title, job_location)
        print(f"Storing job with key: {job_key} in cache key: {cache_key}")
        await redis_client.sadd(cache_key, job_key)

        await redis_client.expire(job_key, 86400)  # Expire in 24 hours
        await redis_client.expire(cache_key, 86400)  # Expire in 24 hours

        return job_key
    except Exception as e:
        print(f"Error while storing job listing: {e}")
        return None
    
if __name__ == '__main__':
    os.environ['FLASK_DEBUG'] = '1'  # Replace FLASK_ENV
    os.environ['FLASK_APP'] = 'app.py'
    app.run(host='0.0.0.0', debug=True, port=3001)  # Indeed scraper port