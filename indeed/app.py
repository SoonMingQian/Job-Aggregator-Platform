import asyncio
from playwright.async_api import async_playwright
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/indeed', methods=['GET'])
def indeed():
    job_title = request.args.get('job_title')
    job_location = request.args.get('job_location')

    if not job_title or not job_location:
        return jsonify({"error": "Missing job_title or job_location parameter"}), 400

    # Run the job search
    results = asyncio.run(main(job_title, job_location))
    
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

async def get_jobs(page):
    try:
        await page.wait_for_selector('a.jcs-JobTitle')
        job_links = page.locator('a.jcs-JobTitle')
        count = await job_links.count()
        
        for i in range(count):
            job_link = job_links.nth(i)
            await job_link.click()
            await page.wait_for_selector('div.jobsearch-ViewJobLayout--embedded')
            
            job_title = await page.locator('h2.jobsearch-JobInfoHeader-title').text_content()
            # company = await page.locator('span.css-1saizt3 e1wnkr790 > a').text_content()
            company = await page.locator('a.css-1ioi40n.e19afand0').text_content()
            if '.c' in company:
                company = company.split('.c')[0]
            company_link = await page.locator('a.css-1ioi40n.e19afand0').get_attribute('href')
            location_div = await page.locator('div[data-testid="inlineHeader-companyLocation"] > div').text_content()
            
            location_parts = location_div.split('•')
            location = location_parts[0].strip()
            work_mode = location_parts[1].strip() if len(location_parts) > 1 else 'N/A'
            
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
            
            print(f"Job ID: {job_id}")
            print(f"Job Title: {job_title}")
            print(f"Company: {company}")
            print(f"Company Link: {company_link}")
            print(f"Location: {location}")
            print(f"Work Mode: {work_mode}")
            print(f"Apply Link: {apply_link}")
            print(f"Job Description: {job_description}")
            
    except Exception as e:
        print(f"Error in get_jobs: {e}")

async def scrape_job_data(job_title, job_location, start, browser):
    context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    page = await context.new_page()
    url = f"https://ie.indeed.com/jobs?q={job_title}&l={job_location}&start={start}"
    await page.goto(url)
    await get_jobs(page)
    await page.close()
    await context.close()
    
async def main(job_title, job_location):
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']  # Disable headless detection
        )
        
        last_page_number = await check_pages(job_title, job_location, browser)
        
        if last_page_number == 1:
            await scrape_job_data(job_title, job_location, 0, browser)
        else:
            tasks = []
            for start in range(0, last_page_number * 10, 10):
                task = asyncio.create_task(scrape_job_data(job_title, job_location, start, browser))
                tasks.append(task)
            await asyncio.gather(*tasks)
        
        await browser.close()

def close_browser(browser):
    print('No page anymore')
    browser.close()

if __name__ == "__main__":
    asyncio.run(main())