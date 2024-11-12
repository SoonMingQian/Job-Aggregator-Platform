from playwright.sync_api import sync_playwright

def open_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False, executable_path=r'C:\Users\Soon Ming Qian\AppData\Local\Google\Chrome\Application\chrome.exe')
    page = browser.new_page()
    page.goto("https://ie.indeed.com/")
    page.wait_for_selector('#text-input-what')
    # Use the unique id to locate the input field for job title and fill it
    page.locator('#text-input-what').fill('software developer internship')
    
    # Use the unique id to locate the input field for location and fill it
    page.locator('#text-input-where').fill('Ireland')
    
    # Click the "Find jobs" button
    page.locator('button.yosegi-InlineWhatWhere-primaryButton[type="submit"]').click()
    return playwright, browser, page

def get_jobs(page, browser):
    try:
        # Wait for the specific button to appear with a timeout of 3 seconds
        page.wait_for_selector('button.css-yi9ndv.e8ju0x51', timeout=3000)
        page.locator('button.css-yi9ndv.e8ju0x51').click()               
    except Exception as e:
        print(f"Button not found or not clickable: {e}")

    # Wait for the search results to load
    page.wait_for_selector('a.jcs-JobTitle')
    
    # Get all job links
    job_links = page.locator('a.jcs-JobTitle')
    count = job_links.count()
    print(count)

    for i in range(count):
        job_link = job_links.nth(i)
        job_link.click()
        page.wait_for_selector('div.jobsearch-ViewJobLayout--embedded')

        # Get the job title
        job_title = page.locator('h2.jobsearch-JobInfoHeader-title').text_content()
        company = page.locator('a.css-1ioi40n.e19afand0').text_content()
        company_link = page.locator('a.css-1ioi40n.e19afand0').get_attribute('href')
        # Get the location and work mode
        location_div = page.locator('div[data-testid="inlineHeader-companyLocation"] > div').text_content()
        location_parts = location_div.split('•')
        location = location_parts[0].strip()
        work_mode = location_parts[1].strip() if len(location_parts) > 1 else 'N/A'
        job_description_element = page.locator('div#jobDescriptionText')
        job_description = ""
        if job_description_element.count() > 0:
            paragraphs = job_description_element.locator('p')
            lists = job_description_element.locator('ul')
            print(paragraphs.count())
            print(lists.count())    
            for i in range(paragraphs.count()):
                job_description += paragraphs.nth(i).inner_text()
                print("paragraphs: " + job_description)
                
            for i in range(lists.count()):
                job_description += lists.nth(i).inner_text() 
                print("lists: " + job_description)
        else:
            job_description = "No job description available"

        print("Overall: " + job_description)

        try:
            apply_link = page.locator('button.css-1234qe1.e8ju0x51').get_attribute('href', timeout=100)
            if apply_link:
                print(f"Apply link: {apply_link}")
            job_id = job_link.get_attribute('data-jk')
            print(job_id)
        except Exception as e:
            print(f"Apply link not found: {e}")
            job_id = job_link.get_attribute('data-jk')
            print(job_id)
            indeed_job_link = 'https://ie.indeed.com/viewjob?jk=' + job_id
            print(f"Indeed job link: {indeed_job_link}")
        
        print(job_title)
        print(company)
        print(company_link)
        print(location)
        print(work_mode)
        print(job_description)

        page.wait_for_selector('a.jcs-JobTitle')
    get_next_page(page, browser)

def get_next_page(page, browser):
    while True:
        try:
            next_page_button = page.locator('a[aria-label="Next Page"]')
            if next_page_button.count() > 0:
                next_page_button.click()
                page.wait_for_timeout(2000)  # Wait for the next page to load
                get_jobs(page, browser)
            else:
                break
        except Exception as e:
            print(f"Error while navigating to the next page: {e}")
            break
    close_browser(browser)
    
def main():
    playwright, browser, page = open_browser()
    try:
        get_jobs(page, browser)
    finally:
        browser.close()
        playwright.stop()

def close_browser(browser):
    print('No page anymore')
    browser.close()

if __name__ == "__main__":
    main()