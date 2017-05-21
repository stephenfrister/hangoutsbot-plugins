import aiohttp
import asyncio
import plugins
import requests
import re
import time

import datetime
from datetime import datetime

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

''' 
Checks Tempostorm for new meta reports and collects data

#https://tempostorm.com
#https://tempostorm.com/hearthstone/meta-snapshot/standard/
'''
    
globalMemoryTempo = "_global_memory_tempo"


def _initialise(bot):
    plugins.register_user_command(["tempo"])
    plugins.start_asyncio_task(_tempo_check)


@asyncio.coroutine
def _tempo_check(bot):
    
    while True:
        
        #yield from asyncio.sleep(60)
        #yield from asyncio.sleep(10000) # 167 minutes (2.77 hours)
        yield from asyncio.sleep(20000) # 334 minutes (5.54 hours)
        
        messageTime = datetime.now().strftime('%H:%M')
        print("_tempo_check started: " + messageTime)
        
        url = "https://tempostorm.com/hearthstone/meta-snapshot/standard/"
        old_date = _get_tempo_latest(bot)
        
        yield from _set_tempo_new_date(bot)
        
        new_date = _get_tempo_latest(bot)
        subs = _get_tempo_subscriptions(bot)
        
        if subs == "Empty":
            subs = []
            
        for conv_id in subs:
            #heartbeat
            #yield from bot.coro_send_message(conv_id, messageTime)
            if new_date != old_date:
                #update data
                yield from _tempo_update_data(bot)
                #post link to chat       
                if new_date != "Empty":
                    messageNew = "New Tempostorm meta-snapshot found: "
                    url += new_date
                    yield from bot.coro_send_message(conv_id, messageNew)
                    yield from bot.coro_send_message(conv_id, url)
                    
    #end _tempo_check


def tempo(bot, event, *args):
    """
    Returns meta information from https://tempostorm.com/
    \nUsage: /h tempo <command>
    \nCommand Options: link, tall, <tier>, data, video, subscribe, unsubscribe
    \nAdmin Options: update, cleanup
    \nTier Options: t1, t2, t3, t4, t5
    """
    messageTier = "Tier Selected: "
    messageInvalid = "Invalid Option. "
    messageUsage = "Usage: /h tempo <command> \n Command Options: link, tall, <tier>, data, video \n Admin Options: update, cleanup \n Tier Options: t1, t2, t3, t4, t5"
    
    ts = ['t1', 't2', 't3', 't4', 't5']
    tiers = ['tier1', 'tier2', 'tier3', 'tier4', 'tier5']
    
    if len(args) > 0:
        
        if args[0].lower() == "data":
            #print("Data")
            
            messageLatest = "Cached Report: " + _get_tempo_latest(bot)
            yield from bot.coro_send_message(event.conv_id, messageLatest)
            
            messageDate = "Checked: " + _get_tempo_date_checked(bot)
            messageDate += " @ " + _get_tempo_time_checked(bot)
            yield from bot.coro_send_message(event.conv_id, messageDate)
            
            return ""
            
        elif args[0].lower() == "resub" or \
              args[0].lower() == "sub" or \
              args[0].lower() == "subscribe":
            #print("Subscribe")
            
            yield from _set_tempo_notification(bot, event, "resub" )
            
            return ""
            
        elif args[0].lower() == "unsub" or \
              args[0].lower() == "unsubscribe":
            #print("Unsubscribe")
            
            yield from _set_tempo_notification(bot, event, "unsub") 
            
            return ""
            
        elif args[0].lower() == "link":
            #print("Link")
            
            url = "https://tempostorm.com/hearthstone/meta-snapshot/standard/"
            date = _get_tempo_latest(bot)
            
            if date != "Empty":
                url += date
                yield from bot.coro_send_message(event.conv_id, url)
            
            return ""
            
        elif args[0].lower() == "video":
            #print("Video")
            
            youtubeUrl = "https://www.youtube.com/watch?v="
            messageVideo = youtubeUrl + _get_tempo_video(bot)
            yield from bot.coro_send_message(event.conv_id, messageVideo)
            
            return ""
            
        elif args[0].lower() == "tall" or args[0].lower() == "tierall":
            #print("Tall")
            
            messageTiers = "All Tiers:"
            yield from bot.coro_send_message(event.conv_id, messageTiers)
            
            yield from _get_tempo_tier_info(bot, event, 't1')
            yield from _get_tempo_tier_info(bot, event, 't2')
            yield from _get_tempo_tier_info(bot, event, 't3')
            yield from _get_tempo_tier_info(bot, event, 't4')
            yield from _get_tempo_tier_info(bot, event, 't5')
            
            return ""
            
        elif args[0].lower() in ts or args[0].lower() in tiers: 
            #print("Tiers")
            
            yield from _get_tempo_tier_info(bot, event, args[0])
            return ""
            
        elif args[0].lower() == "update":
            #print("Update")
            
            messageLong = "Checking for new data. This could take a while..."
            yield from bot.coro_send_message(event.conv_id, messageLong)
            
            yield from _set_tempo_new_date(bot)
            yield from _tempo_update_data(bot)
            
            messageFound= "Latest Found: " + _get_tempo_latest(bot)
            yield from bot.coro_send_message(event.conv_id, messageFound)
            
            messageDone = "Done."
            yield from bot.coro_send_message(event.conv_id, messageDone)
            
            return ""
            
        elif args[0].lower() == "cleanup":
            #print("Cleanup")
            
            _tempo_cleanup(bot)
            messageCleanup = "Cleanup Complete."
            yield from bot.coro_send_message(event.conv_id, messageCleanup)
            
            return ""
            
        elif args[0].lower() == "allthethings":
            #print("AllTheThings")
            
            #data
            messageData = "Cached Report: " + _get_tempo_latest(bot)
            messageData += "\nChecked: " + _get_tempo_date_checked(bot)
            messageData += " @ " + _get_tempo_time_checked(bot)
            yield from bot.coro_send_message(event.conv_id, messageData)
            
            #link
            messageLink = "https://tempostorm.com/hearthstone/meta-snapshot/standard/"
            date = _get_tempo_latest(bot)
            if date != "Empty":
                messageLink += date
                yield from bot.coro_send_message(event.conv_id, messageLink)
            
            #video
            messageVideo = "https://www.youtube.com/watch?v=" 
            messageVideo += _get_tempo_video(bot)
            yield from bot.coro_send_message(event.conv_id, messageVideo)
            
            #tall
            messageTall = "All Tiers:"
            yield from bot.coro_send_message(event.conv_id, messageTall)
            yield from _get_tempo_tier_info(bot, event, 't1')
            yield from _get_tempo_tier_info(bot, event, 't2')
            yield from _get_tempo_tier_info(bot, event, 't3')
            yield from _get_tempo_tier_info(bot, event, 't4')
            yield from _get_tempo_tier_info(bot, event, 't5')
        
            #help
            messageHelp = "Returns meta information from https://tempostorm.com/ \n "
            messageHelp += "Usage: /h tempo <command> \n "
            messageHelp += "Command Options: link, tall, <tier>, data, video, subscribe, unsub \n "
            messageHelp += "Admin Options: update, cleanup \n "
            messageHelp += "Tier Options: t1, t2, t3, t4, t5"
            yield from bot.coro_send_message(event.conv_id, messageHelp)
            
            return ""
        
        else: 
            #print("Invalid")
            print( messageInvalid )
            yield from bot.coro_send_message(event.conv_id, messageInvalid)
            
    else:
        #print("Usage")
        print( messageUsage )
        yield from bot.coro_send_message(event.conv_id, messageUsage)
            
    #end tempo 
    
    
def _tempo_cleanup(bot):
    bot.memory.pop_by_path(["conv_data", globalMemoryTempo])
    bot.conversation_memory_set(globalMemoryTempo, 'cleanup', "complete")
    
def _get_tempo_latest(bot):
    if bot.memory.exists(["conv_data", globalMemoryTempo, 'latest']):
        return bot.conversation_memory_get(globalMemoryTempo, 'latest')
    else: 
        return "Empty"
        
def _get_tempo_date_checked(bot):
    if bot.memory.exists(["conv_data", globalMemoryTempo, 'latest_date_checked']):
        return bot.conversation_memory_get(globalMemoryTempo, 'latest_date_checked')
    else: 
        return "Empty"

def _get_tempo_time_checked(bot):
    if bot.memory.exists(["conv_data", globalMemoryTempo, 'latest_time_checked']):
        return bot.conversation_memory_get(globalMemoryTempo, 'latest_time_checked')
    else: 
        return "Unknown"
        
def _get_tempo_video(bot):
    if bot.memory.exists(["conv_data", globalMemoryTempo, 'video']):
        return bot.conversation_memory_get(globalMemoryTempo, 'video')
    else: 
        return "Empty"
                
def _get_tempo_subscriptions(bot):
    if bot.memory.exists(["conv_data", globalMemoryTempo, 'subscriptions']):
        return bot.conversation_memory_get(globalMemoryTempo, 'subscriptions')
    else: 
        return "Empty"
  
def _set_tempo_subscriptions(bot, command, conv_id):
    subs = _get_tempo_subscriptions(bot)
    if subs == "Empty":
        subs = []
    if command == "add":
        if conv_id not in subs:
            subs.append(conv_id) 
    if command == "remove":
        if conv_id in subs:
            subs.remove(conv_id)
    bot.conversation_memory_set(globalMemoryTempo, 'subscriptions', subs)  
    
def _set_tempo_notification(bot, event, param):    
    if param.lower() == "resub":
        messageSub = "This hangout is set to receive notification when Tempostorm posts new meta analysis. \n To unsubscribe: \n/h tempo unsubscribe"
        _set_tempo_subscriptions(bot, "add", event.conv_id)
        yield from bot.coro_send_message(event.conv_id, messageSub )
        
    if param.lower() == "unsub":
        messageSub = "This hangout will no longer receive notifications of new Tempostorm articles. \n To subscribe: \n/h tempo subscribe"
        _set_tempo_subscriptions(bot, "remove", event.conv_id)
        yield from bot.coro_send_message(event.conv_id, messageSub )

@asyncio.coroutine
def _set_tempo_date_checked(bot):
    mydate = datetime.now().strftime('%Y-%m-%d')
    mytime = datetime.now().strftime('%H:%M')
    bot.conversation_memory_set(globalMemoryTempo, 'latest_date_checked', mydate)
    bot.conversation_memory_set(globalMemoryTempo, 'latest_time_checked', mytime)
    
@asyncio.coroutine
def _set_tempo_video(bot, param):
    bot.conversation_memory_set(globalMemoryTempo, 'video', param)
        
@asyncio.coroutine
def _set_tempo_latest(bot, param):
    bot.conversation_memory_set(globalMemoryTempo, 'latest', param)
    yield from _set_tempo_date_checked(bot)
    
@asyncio.coroutine
def _set_tempo_new_date(bot):
    
    url = "https://tempostorm.com/hearthstone/meta-snapshot/"

    caps = webdriver.DesiredCapabilities().FIREFOX
    caps["marionette"] = False
    driver = webdriver.Firefox(capabilities=caps)
    
    driver.get(url)
    
    # this grabs the redirect page
    while(url == driver.current_url):
        time.sleep(3)
    redirected_url = driver.current_url
    
    # parse the url, get the date, and save it
    url_date = redirected_url.split("/")
    url_len = len(url_date)-1
    
    if url_len >= 0:
        url_end = url_date[url_len]
    else: 
        url_end = "Empty"
    
    yield from _set_tempo_latest(bot, url_end)
    
    driver.quit()
    
@asyncio.coroutine
def _get_tempo_tier_info(bot, event, param):
    
    t1 = bot.conversation_memory_get(globalMemoryTempo, 'decks_t1')
    t2 = bot.conversation_memory_get(globalMemoryTempo, 'decks_t2')
    t3 = bot.conversation_memory_get(globalMemoryTempo, 'decks_t3')
    t4 = bot.conversation_memory_get(globalMemoryTempo, 'decks_t4')
    t5 = bot.conversation_memory_get(globalMemoryTempo, 'decks_t5')
    
    decks = bot.conversation_memory_get(globalMemoryTempo, 'decks')
            
    if param == 't1' or param == 'tier1':
        
        if bot.memory.exists(["conv_data", globalMemoryTempo, 'decks_t1']):
            
            countTier = bot.conversation_memory_get(globalMemoryTempo, 'decks_t1')
            
            message = "Tier 1:"
            
            start = 0
            end = int(countTier) 
            x = 0
            for x in range(start, end):
                message += "\n" + decks[x] 
                x += 1
            
            yield from bot.coro_send_message(event.conv_id, message)
            
        else: 
            yield from bot.coro_send_message(event.conv_id, "Empty")
        
    elif param == 't2' or param == 'tier2':
        if bot.memory.exists(["conv_data", globalMemoryTempo, 'decks_t2']):
            
            countTier = bot.conversation_memory_get(globalMemoryTempo, 'decks_t2')
            
            t1 = bot.conversation_memory_get(globalMemoryTempo, 'decks_t1')
            
            message = "Tier 2: "
            
            start = int(t1)
            end = start + int(countTier) 
            x = 0
            for x in range(start, end):
                message += "\n" + decks[x] 
                x += 1
            
            yield from bot.coro_send_message(event.conv_id, message)
            
        else: 
            yield from bot.coro_send_message(event.conv_id, "Empty")
        
    elif param == 't3' or param == 'tier3':
        if bot.memory.exists(["conv_data", globalMemoryTempo, 'decks_t3']):
            
            countTier = bot.conversation_memory_get(globalMemoryTempo, 'decks_t3')
            
            message = "Tier 3: "
            
            start = int(t1) + int(t2)
            end = start + int(countTier) 
            x = 0
            for x in range(start, end):
                message += "\n" + decks[x] 
                x += 1
            
            yield from bot.coro_send_message(event.conv_id, message)
            
        else: 
            yield from bot.coro_send_message(event.conv_id, "Empty")
        
    elif param == 't4' or param == 'tier4':
        if bot.memory.exists(["conv_data", globalMemoryTempo, 'decks_t4']):
            
            countTier = bot.conversation_memory_get(globalMemoryTempo, 'decks_t4')
            
            message = "Tier 4: "
            
            start = int(t1) + int(t2) + int(t3)
            end = start + int(countTier) 
            x = 0
            for x in range(start, end):
                message += "\n" + decks[x] 
                x += 1
            
            yield from bot.coro_send_message(event.conv_id, message)
            
        else: 
            yield from bot.coro_send_message(event.conv_id, "Empty")
        
    elif param == 't5' or param == 'tier5':
        if bot.memory.exists(["conv_data", globalMemoryTempo, 'decks_t5']):
            
            countTier = bot.conversation_memory_get(globalMemoryTempo, 'decks_t5')
            
            message = "Tier 5:"
            
            start = int(t1) + int(t2) + int(t3) + int(t4)
            end = start + int(countTier) 
            x = 0
            for x in range(start, end):
                message += "\n" + decks[x] 
                x += 1
            
            yield from bot.coro_send_message(event.conv_id, message)
            
        else: 
            yield from bot.coro_send_message(event.conv_id, "Empty")
    
    #end _get_tempo_tier_info
    
@asyncio.coroutine
def _tempo_update_data(bot):
    url = "https://tempostorm.com/hearthstone/meta-snapshot/standard/"
    
    caps = webdriver.DesiredCapabilities().FIREFOX
    caps["marionette"] = False
    driver = webdriver.Firefox(capabilities=caps)
    
    url += _get_tempo_latest(bot)
    print("url: " + url)
    
    driver.get(url)
    
    #wait = WebDriverWait(driver, 10)
    wait = WebDriverWait(driver, 120)
    
    # wait for the page to load
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//div[@class = 'tiers m-b-md']"))
    )
    
    element = driver.find_element_by_xpath("//div[@class='tiers m-b-md']")
    outerhtml = element.get_attribute("outerHTML")
    soup = BeautifulSoup(outerhtml, "lxml")
    
    h4 = soup.find_all('h4')
        
    tier1 = soup.find('div',{'id': 'tier1'})
    tier2 = soup.find('div',{'id': 'tier2'})
    tier3 = soup.find('div',{'id': 'tier3'})
    tier4 = soup.find('div',{'id': 'tier4'})
    tier5 = soup.find('div',{'id': 'tier5'})
    
    t1h4 = tier1.find_all('h4')
    t2h4 = tier2.find_all('h4')
    t3h4 = tier3.find_all('h4')
    t4h4 = tier4.find_all('h4')
    t5h4 = tier5.find_all('h4')
          
    allDecks = []
    
    i = 1
    for deck in h4:
        allDecks.append(str(i) + ": " + deck.text)
        i += 1
    
    bot.conversation_memory_set(globalMemoryTempo, 'decks', allDecks)
    bot.conversation_memory_set(globalMemoryTempo, 'decks_all', str(len(h4)))
    bot.conversation_memory_set(globalMemoryTempo, 'decks_t1', str(len(t1h4)))
    bot.conversation_memory_set(globalMemoryTempo, 'decks_t2', str(len(t2h4)))
    bot.conversation_memory_set(globalMemoryTempo, 'decks_t3', str(len(t3h4)))
    bot.conversation_memory_set(globalMemoryTempo, 'decks_t4', str(len(t4h4)))
    bot.conversation_memory_set(globalMemoryTempo, 'decks_t5', str(len(t5h4)))

    element = driver.find_element_by_xpath("//div[@class='m-t-md']")
    outerhtml = element.get_attribute("outerHTML")
    soup = BeautifulSoup(outerhtml, "lxml")
    
    for iframe in soup.find_all('iframe'):
        frames = iframe.extract()
        source = str(frames.get('src'))
        
        if "youtube" in source:
            url_video = source.split("/")
            yield from _set_tempo_video(bot, url_video[len(url_video)-1])
            
    driver.quit()
    
    #end _tempo_update_data


