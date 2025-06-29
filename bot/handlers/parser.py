import asyncio
import json
import requests
from bs4 import BeautifulSoup
from aiogram import types, Router
from aiogram.filters import Command
from ..config import CHANNEL_ID

BASE_URL = "https://edu.gov.kg/posts/"
CHAT_ID = CHANNEL_ID
STATE_FILE = "state.json"

# Bot instance management
bot = None

def set_bot(new_bot):
    global bot
    bot = new_bot

router = Router()

async def fetch_news(post_id):
    url = f"{BASE_URL}{post_id}"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Use requests with session for better handling
        def make_request():
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(url, timeout=10)
            resp.encoding = 'utf-8'  # Force UTF-8 encoding
            return resp
        
        response = await asyncio.to_thread(make_request)
        print(f"Checking URL: {url}, Status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try multiple title selectors
            title_selectors = [
                "h1",
                "h1.title", 
                "h1.post-title",
                ".title h1",
                ".post-title",
                "[class*='title']",
                "title",
                ".entry-title",
                ".page-title"
            ]
            
            title = None
            for selector in title_selectors:
                title = soup.select_one(selector)
                if title and title.get_text(strip=True):
                    print(f"Title found with selector '{selector}': {title.get_text(strip=True)[:50]}")
                    break
            
            if not title:
                # Try to extract from meta tags
                meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})
                if meta_title:
                    title_text = meta_title.get("content", "")
                    if title_text:
                        title = type('obj', (object,), {'get_text': lambda strip=True: title_text})()
                        print(f"Title found in meta: {title_text[:50]}")
            
            # Try multiple content selectors
            content_selectors = [
                "div.content",
                "div.post-content",
                "div.entry-content", 
                "article",
                "main",
                ".content",
                "[class*='content']",
                "div.description",
                "div.text",
                ".post-body",
                ".entry-body"
            ]
            
            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content and len(content.get_text(strip=True)) > 50:
                    print(f"Content found with selector: {selector}")
                    break
            
            if not content:
                # If no content div found, try to get any text from body
                body = soup.find("body")
                if body:
                    # Get all paragraphs as fallback
                    paragraphs = body.find_all("p")
                    if paragraphs:
                        content_text = " ".join([p.get_text(strip=True) for p in paragraphs[:3]])
                        if len(content_text) > 50:
                            content = type('obj', (object,), {'get_text': lambda strip=True: content_text})()
                            print(f"Content found in paragraphs: {len(content_text)} chars")
            
            print(f"Final - Title: {bool(title)}, Content: {bool(content)}")
            
            if title and content:
                snippet = content.get_text(strip=True)[:200]
                print(f"Success! Snippet: {snippet[:50]}...")
                return {
                    "id": post_id,
                    "title": title.get_text(strip=True),
                    "url": url,
                    "snippet": snippet
                }
            else:
                print(f"Failed - Missing title: {not title}, Missing content: {not content}")
                
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def check_for_new_news(last_id):
    new_items = []
    # Check a wider range and don't break on first failure
    for i in range(last_id + 1, last_id + 20):
        news = await fetch_news(i)
        if news:
            new_items.append(news)
        # Continue checking even if some IDs don't exist
        await asyncio.sleep(0.1)  # Small delay to avoid overwhelming the server
    return new_items

def format_news_message(item):
    return f"📰 <b>{item['title']}</b>\n{item['url']}"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"last_id": 4247}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

async def poll_news():
    while True:
        state = load_state()
        last_id = state["last_id"]
        news = await check_for_new_news(last_id)
        for item in news:
            msg = format_news_message(item)
            await bot.send_message(CHAT_ID, msg, parse_mode="HTML", disable_web_page_preview=False)
            state["last_id"] = item["id"]
        save_state(state)
        await asyncio.sleep(1800)  # Change: now polls every 30 minutes

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Бот запущен и будет проверять новости каждый час!")

@router.message(Command("новоститест"))
async def news_test_cmd(message: types.Message):
    await message.answer("Проверяю новости...")
    
    # Try different starting points
    test_ranges = [4245]
    
    for start_id in test_ranges:
        news = await check_for_new_news(start_id)
        if news:
            response = f"Найдено {len(news)} новостей начиная с ID {start_id}:\n"
            response += "\n".join(f"{item['id']} - {item['title'][:50]}..." for item in news[:3])
            await message.answer(response)
            return
    
    # If no news found, test a single known URL
    test_news = await fetch_news(4500)  # Try a higher ID
    if test_news:
        await message.answer(f"Тест успешен: {test_news['title']}")
    else:
        await message.answer("Новости не найдены. Возможно, изменилась структура сайта.")

@router.message(Command("дебаг"))
async def debug_cmd(message: types.Message):
    """Debug command to inspect a specific page structure"""
    test_id = 4248
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        def make_request():
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(f"{BASE_URL}{test_id}", timeout=10)
            resp.encoding = 'utf-8'
            return resp
            
        response = await asyncio.to_thread(make_request)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check title elements
            titles = soup.find_all(["h1", "h2", "h3"])
            title_info = [f"{t.name}: {t.get_text(strip=True)[:50]}" for t in titles[:5]]
            
            # Check meta tags
            meta_title = soup.find("meta", property="og:title")
            meta_desc = soup.find("meta", property="og:description")
            
            # Find all divs with class attributes
            divs_with_class = soup.find_all("div", class_=True)
            classes = [str(div.get("class"))[:30] for div in divs_with_class[:10]]
            
            response_text = f"URL: {BASE_URL}{test_id}\n"
            response_text += f"Titles found: {title_info}\n"
            response_text += f"Meta title: {meta_title.get('content', 'None') if meta_title else 'None'}\n"
            response_text += f"Meta desc: {meta_desc.get('content', 'None')[:50] if meta_desc else 'None'}\n"
            response_text += f"Classes: {classes[:5]}\n"
            
            await message.answer(response_text)
        else:
            await message.answer(f"Error: {response.status_code}")
    except Exception as e:
        await message.answer(f"Error: {e}")