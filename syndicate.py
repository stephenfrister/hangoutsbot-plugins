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
Returns meta information from Data Reaper Reports

#http://www.vicioussyndicate.com/
#http://www.vicioussyndicate.com/feed/
#http://www.vicioussyndicate.com/vs-data-reaper-report-
'''
    
globalMemoryReaper = "_global_memory_reaper"


def _initialise(bot):
    plugins.register_user_command(["reaper"])
    plugins.start_asyncio_task(_reaper_check)


@asyncio.coroutine
def _reaper_check(bot):
    
    while True:
        
        #yield from asyncio.sleep(60)        
        yield from asyncio.sleep(3600) # 60 minutes (1 hour)
        
        messageTime = datetime.now().strftime('%H:%M')
        print("_reaper_check started: " + messageTime)
    
        vs_rss_url = 'http://www.vicioussyndicate.com/feed/'
        report_url = "http://www.vicioussyndicate.com/vs-data-reaper-report-"
        
        d = feedparser.parse(vs_rss_url)
        
        for entry in d.entries:
            
            # parse the title and check if it's a reaper report
            title = entry.title
            old_report = _get_reaper_latest(bot)
            
            if "vS Data Reaper Report" in title:
                #print(str(title))
                
                # get the link and the report number
                link = entry.link
                url_date = title.split("#")
                url_len = len(url_date)
                
                if(url_len > 1):
                    #print(str(link))
                    
                    rep_num = url_date[url_len-1]
                    last_report = _get_reaper_latest(bot)
                    
                    try:
                        rep_num = int(rep_num)
                    except ValueError:
                        rep_num = last_report
                    
                    # if its a newer report, save it
                    if(rep_num > last_report):
                        yield from _set_reaper_latest(bot, rep_num)
                        
                        
            new_report = _get_reaper_latest(bot)
            subs = _get_reaper_subscriptions(bot)
            
            if subs == "Empty":
                subs = []
                
            for conv_id in subs:
                #heartbeat
                #yield from bot.coro_send_message(conv_id, messageTime)
                if new_report != old_report:
                    #update data
                    print("new_report != old_report")
                    #yield from _reaper_update_data(bot)
                    #post link to chat       
                    if new_report != 0:
                        messageNew = "New Syndicate Reaper Report found: "
                        report_url += str(new_report)
                        yield from bot.coro_send_message(conv_id, messageNew)
                        yield from bot.coro_send_message(conv_id, report_url)
                    
    #end _reaper_check


def reaper(bot, event, *args):
    """
    Returns meta information from http://www.vicioussyndicate.com/
    Usage: /h reaper <command>
    \nCommand Options: data, link, distribution, frequency, winrates, subscribe, unsubscribe
    \nAdmin Options: update, cleanup
    \nUnwritten Options: 
    
    """
    
    messageInvalid = "Invalid Option. "
    messageUsage = "Usage: "
    
    if len(args) > 0:
        
        if args[0].lower() == "data":
            #print("Data")
            
            messageLatest = "Latest Report: "
            url = "http://www.vicioussyndicate.com/vs-data-reaper-report-"
            report = _get_reaper_latest(bot)
            
            if report != 0:
                url += str(report)
                messageLatest += url
                yield from bot.coro_send_message(event.conv_id, messageLatest)
                
                messageDate = "Checked: " + _get_reaper_date_checked(bot)
                messageDate += " @ " + _get_reaper_time_checked(bot)
                yield from bot.coro_send_message(event.conv_id, messageDate)
            
            else:
                messageDate = "No report found at this time."
                yield from bot.coro_send_message(event.conv_id, messageDate)
                     
            return ""
            
        elif args[0].lower() == "resub" or \
              args[0].lower() == "sub" or \
              args[0].lower() == "subscribe":
            #print("Subscribe")
            yield from _set_reaper_notification(bot, event, "resub" )
            
            return ""
            
        elif args[0].lower() == "unsub" or \
              args[0].lower() == "unsubscribe":
            #print("Unsubscribe")
            yield from _set_reaper_notification(bot, event, "unsub") 
            
            return ""
            
        elif args[0].lower() == "link":
            #print("Link")
            
            url = "http://www.vicioussyndicate.com/vs-data-reaper-report-"
            report = _get_reaper_latest(bot)
            
            if report != 0:
                url += str(report)
                yield from bot.coro_send_message(event.conv_id, url)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
            return ""
            
        elif args[0].lower() == "distribution":
            #print("Distribution")
            report = _get_reaper_latest(bot)
            image = "http://www.vicioussyndicate.com/wp-content/uploads/DRR"
            image += str(report)
            image += "-Distribution-All.png"
            if report != 0:
                yield from _print_image(bot, event, image)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
        elif args[0].lower() == "frequency":
            #print("Frequency")
            report = _get_reaper_latest(bot)
            image = "http://www.vicioussyndicate.com/wp-content/uploads/DRR"
            image += str(report)
            image += "-Frequency-Days.png"
            if report != 0:
                yield from _print_image(bot, event, image)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
        elif args[0].lower() == "winrates" or \
              args[0].lower() == "winrate":
            #print("Winrates")
            report = _get_reaper_latest(bot)
            image = "http://www.vicioussyndicate.com/wp-content/uploads/DRR"
            image += str(report)
            image += "-Winrates.png"
            if report != 0:
                yield from _print_image(bot, event, image)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
                
        elif args[0].lower() == "update":
            #print("Update")
            
            messageLong = "Checking for new data..."
            yield from bot.coro_send_message(event.conv_id, messageLong)
            
            yield from _reaper_update_data(bot)
            
            url = "http://www.vicioussyndicate.com/vs-data-reaper-report-"
            report = _get_reaper_latest(bot)
            
            if report != 0:
                url += str(report)
                messageFound= "Latest Found: " + url
                yield from bot.coro_send_message(event.conv_id, messageFound)
            else: 
                messageFound= "Try again later."
                yield from bot.coro_send_message(event.conv_id, messageFound)
                    
            messageDone = "Done."
            yield from bot.coro_send_message(event.conv_id, messageDone)
            
            return ""
            
        elif args[0].lower() == "cleanup":
            #print("Cleanup")
            
            _reaper_cleanup(bot)
            messageCleanup = "Cleanup Complete."
            yield from bot.coro_send_message(event.conv_id, messageCleanup)
            
            return ""
            
        elif args[0].lower() == "allthethings":
            #print("AllTheThings")

            messageLatest = "Latest Report: "
            url = "http://www.vicioussyndicate.com/vs-data-reaper-report-"
            report = _get_reaper_latest(bot)
            
            if report != 0:
                url += str(report)
                messageLatest += url
                yield from bot.coro_send_message(event.conv_id, messageLatest)
                
                messageDate = "Checked: " + _get_reaper_date_checked(bot)
                messageDate += " @ " + _get_reaper_time_checked(bot)
                yield from bot.coro_send_message(event.conv_id, messageDate)
            
            else:
                messageDate = "No report found at this time."
                yield from bot.coro_send_message(event.conv_id, messageDate)

            image = "http://www.vicioussyndicate.com/wp-content/uploads/DRR"
            image += str(report)
            image += "-Distribution-All.png"
            
            if report != 0:
                yield from _print_image(bot, event, image)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
            image = "http://www.vicioussyndicate.com/wp-content/uploads/DRR"
            image += str(report)
            image += "-Frequency-Days.png"
            
            if report != 0:
                yield from _print_image(bot, event, image)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
            
            image = "http://www.vicioussyndicate.com/wp-content/uploads/DRR"
            image += str(report)
            image += "-Winrates.png"
            
            if report != 0:
                yield from _print_image(bot, event, image)
            else: 
                messageNope = "Nope."
                yield from bot.coro_send_message(event.conv_id, messageNope)
        
        else: 
            #print("Invalid")
            print( messageInvalid )
            yield from bot.coro_send_message(event.conv_id, messageInvalid)
            
    else:
        #print("Usage")
        print( messageUsage )
        yield from bot.coro_send_message(event.conv_id, messageUsage)
            
    #end reaper
    
    
def _print_image(bot, event, image):
    """
    Print report images to chat
    """ 
    context = {
        "parser": False,
    }

    filename = os.path.basename(image)
    
    request = yield from aiohttp.request('get', image )
    raw = yield from request.read()
    image_data = io.BytesIO(raw)
    image_id = yield from bot._client.upload_image(image_data, filename=filename)
    
    yield from bot.coro_send_message(event.conv.id_, "Reqested Data.", context, image_id=image_id) 
    
    return ""
    
    #end _print_image
    
    
def _reaper_cleanup(bot):
    bot.memory.pop_by_path(["conv_data", globalMemoryReaper])
    bot.conversation_memory_set(globalMemoryReaper, 'cleanup', "complete")
    
def _get_reaper_latest(bot):
    if bot.memory.exists(["conv_data", globalMemoryReaper, 'latest']):
        return bot.conversation_memory_get(globalMemoryReaper, 'latest')
    else: 
        return 0
        
def _get_reaper_date_checked(bot):
    if bot.memory.exists(["conv_data", globalMemoryReaper, 'latest_date_checked']):
        return bot.conversation_memory_get(globalMemoryReaper, 'latest_date_checked')
    else: 
        return "Empty"

def _get_reaper_time_checked(bot):
    if bot.memory.exists(["conv_data", globalMemoryReaper, 'latest_time_checked']):
        return bot.conversation_memory_get(globalMemoryReaper, 'latest_time_checked')
    else: 
        return "Unknown"

def _get_reaper_subscriptions(bot):
    if bot.memory.exists(["conv_data", globalMemoryReaper, 'subscriptions']):
        return bot.conversation_memory_get(globalMemoryReaper, 'subscriptions')
    else: 
        return "Empty"
  
def _set_reaper_subscriptions(bot, command, conv_id):
    subs = _get_reaper_subscriptions(bot)
    if subs == "Empty":
        subs = []
    if command == "add":
        if conv_id not in subs:
            subs.append(conv_id) 
    if command == "remove":
        if conv_id in subs:
            subs.remove(conv_id)
    bot.conversation_memory_set(globalMemoryReaper, 'subscriptions', subs)  
    
def _set_reaper_notification(bot, event, param):    
    if param.lower() == "resub":
        messageSub = "This hangout is set to receive notification when new Data Reaper Reports are available. \n To unsubscribe: \n/h reaper unsubscribe"
        _set_reaper_subscriptions(bot, "add", event.conv_id)
        yield from bot.coro_send_message(event.conv_id, messageSub )
        
    if param.lower() == "unsub":
        messageSub = "This hangout will no longer receive notifications of new Data Reaper Reports. \n To subscribe: \n/h reaper subscribe"
        _set_treaper_subscriptions(bot, "remove", event.conv_id)
        yield from bot.coro_send_message(event.conv_id, messageSub )

@asyncio.coroutine
def _set_reaper_date_checked(bot):
    mydate = datetime.now().strftime('%Y-%m-%d')
    mytime = datetime.now().strftime('%H:%M')
    bot.conversation_memory_set(globalMemoryReaper, 'latest_date_checked', mydate)
    bot.conversation_memory_set(globalMemoryReaper, 'latest_time_checked', mytime)
    
@asyncio.coroutine
def _set_reaper_latest(bot, param):
    bot.conversation_memory_set(globalMemoryReaper, 'latest', param)
    yield from _set_reaper_date_checked(bot)
    
@asyncio.coroutine
def _reaper_update_data(bot):

    vs_rss_url = 'http://www.vicioussyndicate.com/feed/'
    report_url = "http://www.vicioussyndicate.com/vs-data-reaper-report-"

    d = feedparser.parse(vs_rss_url)

    for entry in d.entries:
        
        # parse the title and check if it's a reaper report
        title = entry.title
        old_report = _get_reaper_latest(bot)
        
        if "vS Data Reaper Report" in title:
            #print(str(title))
            
            # get the link and the report number
            link = entry.link
            url_date = title.split("#")
            url_len = len(url_date)
            
            if(url_len > 1):
                #print(str(link))
                
                rep_num = url_date[url_len-1]
                last_report = _get_reaper_latest(bot)
                
                try:
                    rep_num = int(rep_num)
                except ValueError:
                    rep_num = last_report
                
                # if its a newer report, save it
                if(rep_num > last_report):
                    yield from _set_reaper_latest(bot, rep_num)
                    
    #end _reaper_update_data

