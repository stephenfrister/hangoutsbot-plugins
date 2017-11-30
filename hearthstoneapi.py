import aiohttp
import asyncio
import io
import os.path
import plugins
import requests
import re
import time

import hangups

from bs4 import BeautifulSoup
from datetime import datetime
from commands import command

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

''' 
Uses API data from the locations below

Requires a Mashape api key to be saved in the config.json file
to be consumed here as the variable hearthstone_api_key
Use the admin command setapikey to 

#http://hearthstoneapi.com/#data
#https://market.mashape.com/omgvamp/hearthstone#
'''

globalMemoryHearth = "_global_memory_hearth"


def _initialise(bot):
    #plugins.register_user_command(["card", "test"])
    plugins.register_user_command(["card"])
    plugins.register_handler(_handle_dot_events, type="message")
    
    
def _handle_dot_events(bot, event, command):
    
    """Handle keywords in messages"""

    if isinstance(event.conv_event, hangups.ChatMessageEvent):
        event_type = "MESSAGE"
        
        #print("message") 
        if _words_in_text(".card", event.text):
            cardargs = event.text.split(".card")
            #print(".card len[0]: " + cardargs[0]) 
            #print(".card len[1]: " + cardargs[1]) 
            
            yield from card(bot, event, cardargs[1].strip() )
    
    #end _handle_dot_events
        

def _words_in_text(word, text):
    """Return True if word is in text"""

    if word.startswith("regex:"):
        word = word[6:]
    else:
        word = re.escape(word)

    regexword = "(?<!\w)" + word + "(?!\w)"

    return True if re.search(regexword, text, re.IGNORECASE) else False
    
    #end _words_in_text
    
    
@command.register(admin=True)
def setapikey(bot, event, *args):
    """
    Use to set your api key needed to access the hearthstoneapi data
    Get from mashape at https://market.mashape.com/omgvamp/hearthstone#
    Usage: /h setapikey <key>
    """    
    if len(args) == 1:
        bot.conversation_memory_set(globalMemoryHearth, 'hearthstone_api_key', args[0])  
        messageUsage = "API key set"
        yield from bot.coro_send_message(event.conv_id, messageUsage)
    else:
        messageUsage = "Usage: /h setapikey <key>"
        yield from bot.coro_send_message(event.conv_id, messageUsage)
    print("echoid")
    
    #end setapikey


def card(bot, event, *args):
    """
    Returns Hearthstone card information from http://hearthstoneapi.com/
    Usage: /h card <name>
    Example: /h card leeroy jenkins
    """    
    #Example: /h card 2 ysera
    messageUsage = "Usage: /h card <name> \n Example: /h card leeroy jenkins"
    
    string_match = ""; 
    if len(args) > 0:
        for x in range(0, len(args) ):
            string_match += args[x]
            x += 1
    
        cards = _get_card_info(bot, args)
        
        message0 = "Sorry! Sorry. I'm sorry, sorry. I didn't find anything."
        message1 = "Here's what I found:"
        message2 = "I found multiple matches. Can you be more specific?" 
        #message5 = "More than 5 matches. You'll need to be more specific."
        message10 = "More than 10 matches. You'll need to be more specific."
        messageTry = "I am going to try and print this one for you: "
        
        context = {
            "parser": False,
        }
        
        if cards:
            if len(cards) < 0:
                yield from bot.coro_send_message(event.conv_id, message0)
                
            elif len(cards) == 1:
                yield from bot.coro_send_message(event.conv_id, message1)
         
                yield from _print_card(bot, event, cards, 0)
                        
            #elif 2 <= len(cards) <= 5:
            elif 2 <= len(cards) <= 10:
                yield from bot.coro_send_message(event.conv_id, message2)
                for x in range(0, len(cards) ):
                    yield from bot.coro_send_message(event.conv_id, str(cards[x]['name']) )
                    if str(cards[x]['name']).lower() == string_match.lower():
                        matchPrint = messageTry + cards[x]['name']
                        yield from bot.coro_send_message(event.conv_id, matchPrint)
                        yield from _print_card(bot, event, cards, x)
                    x += 1
            else:
                #yield from bot.coro_send_message(event.conv_id, message5)
                yield from bot.coro_send_message(event.conv_id, message10)
                
        else:
            yield from bot.coro_send_message(event.conv_id, message0)
        
    else: 
        yield from bot.coro_send_message(event.conv_id, messageUsage)
        
    #end cards


def _print_card(bot, event, cards, index):
    """
    Print cards to chat 
    """ 
    context = {
        "parser": False,
    }

    filename = os.path.basename(str(cards[index]['img']) )
    
    request = yield from aiohttp.request('get', str(cards[index]['img']) )
    raw = yield from request.read()
    image_data = io.BytesIO(raw)
    image_id = yield from bot._client.upload_image(image_data, filename=filename)
    
    yield from bot.coro_send_message(event.conv.id_, str(cards[index]['cardSet']), context, image_id=image_id) 
    
    return ""
    
    #end _print_card


def _get_card_info(bot, params):
    """
    Finds cards using the api
    """
    #api_key = bot.get_config_option('hearthstone_api_key')
    hearthstone_api_url = 'https://omgvamp-hearthstone-v1.p.mashape.com/cards/search/'
    
    if bot.memory.exists(["conv_data", globalMemoryHearth, 'hearthstone_api_key']):
        api_key = bot.conversation_memory_get(globalMemoryHearth, 'hearthstone_api_key')
    
        if len(params) > 0:
            for x in range(0, len(params) ):
                hearthstone_api_url += str(params[x])
                y = len(params) - 1
                if x < y:
                    hearthstone_api_url += str("%20")
                #print(str(x) + ": " + params[x]) 
                x += 1
        else:
            return ""
        
        response = requests.get(hearthstone_api_url,
            headers={ "X-Mashape-Key": api_key }
        )
        
        try:
            
            data = response.json()
            print( str( data ) )
            
            for x in range( len(data), 0, -1):
                
                # remove any cards in the debug set
                if str(data[x-1]['cardSet']) == "Debug" :
                    #print("deleting: " + str(data[x-1]) )
                    del data[x-1]
                
                # remove all cards without images
                if "img" not in str(data[x-1]):
                    #print("deleting: " + str(data[x-1]) )
                    del data[x-1]
                
            if 'error' in data:  
                print( "Error" )   
                return ""
            
            #print( str( data ) )
            return data 
            
        except (IndexError, KeyError):
            #logger.error('unable to parse address return data: %d: %s', resp.status_code, resp.json())
            print( "Error, unable to parse" )  
            return  ""
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout):
            #logger.error('unable to connect with omgvamp-hearthstone-v1.p.mashape.com: %d - %s', resp.status_code, resp.text) 
            print( "Error, unable to connect" )  
            return  ""
    
    else:            
        #logger.error('no api key found, hearthstone_api_key required, use: setapi <key>) 
        print( "Error, hearthstone_api_key required" ) 
        print( "Use 'setapikey' command" )  
    
    return  ""
    
    #end _get_card_info
    
    
