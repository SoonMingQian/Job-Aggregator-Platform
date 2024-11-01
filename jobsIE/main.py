from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.jobs.ie/")
        search_jobs(page, browser)

def search_jobs(page, browser):
    cookies(page)

    # Search for jobs
    page.wait_for_selector('#stepstone-autocomplete-150')
    page.locator('#stepstone-autocomplete-150').fill('parttime')
    page.locator('#stepstone-autocomplete-155').fill('Ireland')
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
            job_title = job_listing.locator('a[data-testid="job-item-title"] .res-nehv70').text_content()
            apply_link = job_listing.locator('a[data-testid="job-item-title"]').get_attribute('href')
            company = job_listing.locator('span[data-at="job-item-company-name"]').text_content()
            location = job_listing.locator('span[data-at="job-item-location"]').text_content()
            content = job_listing.locator('div[data-at="jobcard-content"]').text_content()

            print(job_title)
            print(apply_link)
            print(company)
            print(location)
            print(content)
        
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

def close(browser):
    while True:
        continue

    browser.close()
run()