import aiohttp
import asyncio
import io
import os.path
import plugins
import re
import time
import feedparser

from datetime import datetime
from bs4 import BeautifulSoup


''' 
Returns tavern brawl information from Hearthstone Top Decks

#http://www.hearthstonetopdecks.com/
#http://www.hearthstonetopdecks.com/feed/

#http://www.hearthstonetopdecks.com/category/tavern-brawl/
#http://www.hearthstonetopdecks.com/category/tavern-brawl/feed/


https://hearthstone.gamepedia.com/Tavern_Brawl
Tavern Brawl Schedule:

Region          Open                Close
Americas        Wed 9:00 AM PST     Mon 3:00 AM PST
Europe          Wed 10:00 PM CET    Mon 6:00 AM CET
Taiwan/China    Thu 5:00 AM CST     Mon 6:00 AM CST
Korea           Thu 6:00 AM KST     Mon 7:00 AM KST

'''
    
globalMemoryBrawl = "_global_memory_tavern_brawl"


def _initialise(bot):
    plugins.register_user_command(["brawl"])
    plugins.start_asyncio_task(_brawl_check)
    plugins.start_asyncio_task(_brawl_check_alarm)


@asyncio.coroutine
def _brawl_check_alarm(bot):
    
    while True:
        
        #yield from asyncio.sleep(30) 
        yield from asyncio.sleep(6000)
        
        check_day = datetime.today().weekday()
        check_time = datetime.now().hour
        alarm_set = _get_brawl_reminder(bot)
        
        ## if monday
        ## if alarm hasn't already been set
        ## set reminder
        
        if(alarm_set == 0):
            if(check_day == 0):
                if(check_time > 12):
                    yield from _set_brawl_reminder(bot, 1)
                    
        ## if sunday
        ## if past noon
        ## if alarm hasn't already been triggered
        ## send reminder

        #if(alarm_set == 1):
        else: 
            if(check_day == 6):
                if(check_time > 12):
                    #print("send a notification")
                    
                    latest_brawl = _get_brawl_latest(bot)
                    subs = _get_brawl_subscriptions(bot)
                    
                    if subs == "Empty":
                        subs = []
                        
                    #post link to chat 
                    for conv_id in subs: 
                        if latest_brawl != "Empty":
                            
                            messageCheck = "Tavern Brawl: "
                            yield from bot.coro_send_message(conv_id, messageCheck)                            
                            yield from bot.coro_send_message(conv_id, latest_brawl) 
                            messageCheck = "Event ends later tonight."                         
                            yield from bot.coro_send_message(conv_id, messageCheck)
                    
                    yield from _set_brawl_reminder(bot, 0)
                    
    #end _brawl_check_alarm
    
    
@asyncio.coroutine
def _brawl_check(bot):
    
    while True:
        
        #yield from asyncio.sleep(60)        
        yield from asyncio.sleep(3900) # 65 minutes (1 hour)
        
        messageTime = datetime.now().strftime('%H:%M')
        print("_brawl_check started: " + messageTime)
    
        vs_rss_url = 'http://www.hearthstonetopdecks.com/category/tavern-brawl/feed/'
        
        d = feedparser.parse(vs_rss_url)
        
        old_brawl = _get_brawl_latest(bot)        
        latest_datetime = _get_brawl_datetime(bot)
        
        for entry in d.entries:
            
            # parse the title and check if it's a brawl report
            title = entry.title
            link = entry.link
            description = entry.description
            entry_date = time.strftime("%Y%m%d", entry.updated_parsed)
            
            if "Tavern Brawl" in title:
                
                title = title[13:]
                
                description = description.split('</p>')[0]
                description = description.replace('<p>','')
                description = description.replace('&#8217;','')
                description = description.replace('[&#8230;]','...')
                
                if(latest_datetime == "Empty"):
                    print("latest_datetime == 'Empty'")
                    
                    yield from _set_brawl_latest(bot, title)
                    yield from _set_brawl_link(bot, link)
                    yield from _set_brawl_datetime(bot, entry_date)
                    yield from _set_brawl_description(bot, description)
                    
                    latest_datetime = _get_brawl_datetime(bot)
                
                elif(entry_date > latest_datetime): 
                    print("entry_date > latest_datetime. ")
                    
                    yield from _set_brawl_latest(bot, title)
                    yield from _set_brawl_link(bot, link)
                    yield from _set_brawl_datetime(bot, entry_date)
                    yield from _set_brawl_description(bot, description)
                    
                    latest_datetime = _get_brawl_datetime(bot)
                    
                    
        latest_brawl = _get_brawl_latest(bot)
        subs = _get_brawl_subscriptions(bot)
        
        if subs == "Empty":
            subs = []
            
        if latest_brawl != old_brawl:
            #post link to chat 
            for conv_id in subs: 
                if latest_brawl != "Empty":
                    messageNew = "New Tavern Brawl is up: "
                    
                    link = _get_brawl_link(bot)
                    
                    yield from bot.coro_send_message(conv_id, messageNew)
                    yield from bot.coro_send_message(conv_id, latest_brawl)
                    yield from bot.coro_send_message(conv_id, link)
        
        yield from _set_brawl_date_checked(bot)
                    
    #end _brawl_check


def brawl(bot, event, *args):
    """
    Returns articles on new Tavern Brawls from http://www.hearthstonetopdecks.com
    \nUsage: /h brawl <command>
    \nCommand Options: link, title, description, subscribe, unsubscribe
    \nAdmin Options: update, cleanup
    """
    
    #\nCommand Options: link, title, description, subscribe, unsubscribe, allthethings
    #\nAdmin Options: update, cleanup
    
    messageInvalid = "Invalid Option. "
    
    #help
    messageUsage = "Usage: /h brawl <command> \n "
    messageUsage += "Command Options: link, title, description, subscribe, unsubscribe \n "
    messageUsage += "Admin Options: update, cleanup"
    
    if len(args) > 0:
        
        if args[0].lower() == "data":
            #print("Data")
            
            title = _get_brawl_latest(bot)
            link = _get_brawl_link(bot)
            
            messageLatest = "Latest Tavern Brawl:"
            
            if title != "Empty":
                yield from bot.coro_send_message(event.conv_id, messageLatest)
                yield from bot.coro_send_message(event.conv_id, title)
                yield from bot.coro_send_message(event.conv_id, link)
                
                messageDate = "Checked: " + _get_brawl_date_checked(bot)
                messageDate += " @ " + _get_brawl_time_checked(bot)
                yield from bot.coro_send_message(event.conv_id, messageDate)
            
            else:
                messageDate = "No report found at this time."
                yield from bot.coro_send_message(event.conv_id, messageDate)
                     
            return ""
            
        elif args[0].lower() == "resub" or \
              args[0].lower() == "sub" or \
              args[0].lower() == "subscribe":
            #print("Subscribe")
            yield from _set_brawl_notification(bot, event, "resub" )
            
            return ""
            
        elif args[0].lower() == "unsub" or \
              args[0].lower() == "unsubscribe":
            #print("Unsubscribe")
            yield from _set_brawl_notification(bot, event, "unsub") 
            
            return ""
            
        elif args[0].lower() == "link":
            #print("Link")
            
            link = _get_brawl_link(bot)
            
            if link != "Empty":
                yield from bot.coro_send_message(event.conv_id, link)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
            return ""
            
        elif args[0].lower() == "description" or \
              args[0].lower() == "desc":
            #print("Description")
            
            description = _get_brawl_description(bot)
            
            if description != "Empty":
                yield from bot.coro_send_message(event.conv_id, description)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
            return ""
            
        elif args[0].lower() == "title":
            #print("Title")
            
            title = _get_brawl_latest(bot)
            
            if title != "Empty":
                yield from bot.coro_send_message(event.conv_id, title)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
            return ""
                
        elif args[0].lower() == "update":
            #print("Update")
            
            messageLong = "Checking for new data..."
            yield from bot.coro_send_message(event.conv_id, messageLong)
            
            yield from _brawl_update_data(bot)
            
            title = _get_brawl_latest(bot)
            link = _get_brawl_link(bot)
            
            if title != "Empty":
                messageFound= "Latest Tavern Brawl: "
                yield from bot.coro_send_message(event.conv_id, messageFound)
                yield from bot.coro_send_message(event.conv_id, title)
                yield from bot.coro_send_message(event.conv_id, link)
            else: 
                messageFound= "Try again later."
                yield from bot.coro_send_message(event.conv_id, messageFound)
                    
            messageDone = "Done."
            yield from bot.coro_send_message(event.conv_id, messageDone)
            
            return ""
            
        elif args[0].lower() == "cleanup":
            #print("Cleanup")
            
            _brawl_cleanup(bot)
            messageCleanup = "Cleanup Complete."
            yield from bot.coro_send_message(event.conv_id, messageCleanup)
            
            return ""

        else: 
            #print("Invalid")
            print( messageInvalid )
            yield from bot.coro_send_message(event.conv_id, messageInvalid)
            
            print( messageUsage )
            yield from bot.coro_send_message(event.conv_id, messageUsage)
            
    else:
        #print("Usage")
        print( messageUsage )
        yield from bot.coro_send_message(event.conv_id, messageUsage)
            
    #end brawl
    
    
def _brawl_cleanup(bot):
    bot.memory.pop_by_path(["conv_data", globalMemoryBrawl])
    bot.conversation_memory_set(globalMemoryBrawl, 'cleanup', "complete")
    
def _get_brawl_latest(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'latest']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'latest')
    else: 
        return "Empty"
        
def _get_brawl_datetime(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'datetime']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'datetime')
    else: 
        return "Empty"
        
def _get_brawl_link(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'link']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'link')
    else: 
        return "Empty"
        
def _get_brawl_description(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'description']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'description')
    else: 
        return "Empty"
        
def _get_brawl_date_checked(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'latest_date_checked']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'latest_date_checked')
    else: 
        return "Empty"

def _get_brawl_time_checked(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'latest_time_checked']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'latest_time_checked')
    else: 
        return "Unknown"

def _get_brawl_subscriptions(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'subscriptions']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'subscriptions')
    else: 
        return "Empty"
        
def _get_brawl_reminder(bot):
    if bot.memory.exists(["conv_data", globalMemoryBrawl, 'alarm']):
        return bot.conversation_memory_get(globalMemoryBrawl, 'alarm')
    else: 
        return 0
        
@asyncio.coroutine
def _set_brawl_reminder(bot, param):
    bot.conversation_memory_set(globalMemoryBrawl, 'alarm', param)
        
def _set_brawl_subscriptions(bot, command, conv_id):
    subs = _get_brawl_subscriptions(bot)
    if subs == "Empty":
        subs = []
    if command == "add":
        if conv_id not in subs:
            subs.append(conv_id) 
    if command == "remove":
        if conv_id in subs:
            subs.remove(conv_id)
    bot.conversation_memory_set(globalMemoryBrawl, 'subscriptions', subs)  
        
@asyncio.coroutine
def _set_brawl_notification(bot, event, param):    
    if param.lower() == "resub":
        messageSub = "This hangout is set to receive notification when new Tavern Brawls are available. \n To unsubscribe: \n/h brawl unsubscribe"
        _set_brawl_subscriptions(bot, "add", event.conv_id)
        yield from bot.coro_send_message(event.conv_id, messageSub )
        
    if param.lower() == "unsub":
        messageSub = "This hangout will no longer receive notifications of new Tavern Brawls. \n To subscribe: \n/h brawl subscribe"
        _set_brawl_subscriptions(bot, "remove", event.conv_id)
        yield from bot.coro_send_message(event.conv_id, messageSub )
        
@asyncio.coroutine
def _set_brawl_date_checked(bot):
    mydate = datetime.now().strftime('%Y-%m-%d')
    mytime = datetime.now().strftime('%H:%M')
    bot.conversation_memory_set(globalMemoryBrawl, 'latest_date_checked', mydate)
    bot.conversation_memory_set(globalMemoryBrawl, 'latest_time_checked', mytime)
    
@asyncio.coroutine
def _set_brawl_latest(bot, param):
    
    bot.conversation_memory_set(globalMemoryBrawl, 'latest', param)
    
    mydate = datetime.now().strftime('%Y-%m-%d')
    mytime = datetime.now().strftime('%H:%M')
    bot.conversation_memory_set(globalMemoryBrawl, 'latest_date_found_on', mydate)
    bot.conversation_memory_set(globalMemoryBrawl, 'latest_time_found_on', mytime)
    
    yield from _set_brawl_date_checked(bot)

@asyncio.coroutine
def _set_brawl_link(bot, param):
    bot.conversation_memory_set(globalMemoryBrawl, 'link', param)
    
@asyncio.coroutine
def _set_brawl_description(bot, param):
    bot.conversation_memory_set(globalMemoryBrawl, 'description', param)
    
@asyncio.coroutine
def _set_brawl_datetime(bot, param):
    bot.conversation_memory_set(globalMemoryBrawl, 'datetime', param)
    
@asyncio.coroutine
def _brawl_update_data(bot):

    vs_rss_url = 'http://www.hearthstonetopdecks.com/category/tavern-brawl/feed/'
    
    d = feedparser.parse(vs_rss_url)
       
    latest_datetime = _get_brawl_datetime(bot)

    for entry in d.entries:
        
        # parse the title and check if it's a brawl report
        title = entry.title
        link = entry.link
        description = entry.description
        entry_date = time.strftime("%Y%m%d", entry.updated_parsed)
        
        if "Tavern Brawl" in title:
            
            title = title[13:]
            
            description = description.split('</p>')[0]
            description = description.replace('<p>','')
            description = description.replace('&#8217;','')
            description = description.replace('[&#8230;]','...')
            
            if(latest_datetime == "Empty"):
                print("latest_datetime == 'Empty'")
                
                yield from _set_brawl_latest(bot, title)
                yield from _set_brawl_link(bot, link)
                yield from _set_brawl_datetime(bot, entry_date)
                yield from _set_brawl_description(bot, description)
                
                latest_datetime = _get_brawl_datetime(bot)
            
            elif(entry_date > latest_datetime): 
                print("entry_date > latest_datetime. ")
                
                yield from _set_brawl_latest(bot, title)
                yield from _set_brawl_link(bot, link)
                yield from _set_brawl_datetime(bot, entry_date)
                yield from _set_brawl_description(bot, description)
                
                latest_datetime = _get_brawl_datetime(bot)
            
    #end _brawl_update_data


