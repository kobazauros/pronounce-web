import pytest
from playwright.sync_api import Page, expect

def test_homepage_loads(page: Page):
    """
    Verify the homepage loads and displays the correct title.
    """
    page.goto("http://127.0.0.1:5000/")
    expect(page).to_have_title("Pronunciation Checker (Thesis Edition)")

def test_student_info_entry(page: Page):
    """
    Verify that entering student info enables the word list interaction.
    """
    page.goto("http://127.0.0.1:5000/")
    
    # 1. Enter Student Name and ID
    page.fill("#student-name", "Edge Tester")
    page.fill("#student-id", "999999")
    
    # 2. Click a word (e.g., the first one)
    # Note: Words are loaded via fetch, so we wait for the list to populate
    word_link = page.locator("#word-list .word-link").first
    expect(word_link).to_be_visible(timeout=5000)
    word_text = word_link.text_content()
    
    word_link.click()
    
    # 3. Verify "Sample Pronunciation" updates
    sample_header = page.locator("#sample-word-placeholder")
    expect(sample_header).to_have_text(word_text)
    
    # 4. Verify "Play Sample" button is present
    play_btn = page.locator("#play-sample")
    expect(play_btn).to_be_visible()

def test_initial_state(page: Page):
    """
    Verify initial disabled states of buttons.
    """
    page.goto("http://127.0.0.1:5000/")
    
    # "Stop Recording" should be disabled initially
    expect(page.locator("#record-stop")).to_be_disabled()
    
    # "Play Recording" should be disabled initially
    expect(page.locator("#play-user")).to_be_disabled()
    
    # "Submit" should be disabled initially
    expect(page.locator("#submit-recording")).to_be_disabled()
