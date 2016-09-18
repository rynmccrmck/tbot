import os
import sys
import json
import pylru
import time

import requests
from flask import Flask, request

app = Flask(__name__)

size = 10000
cache = pylru.lrucache(size)

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    welcome = "Welcome to Toronto Services Wayfinding! We're here to help you find the resources you need. What are you looking for?"
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
        	
    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
	
                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text	
                    
		    try:
		        if str(sender_id) not in cache.keys():
			    cache[sender_id] = {"purpose":"na"}
			    time.sleep(2)
                            send_message(sender_id, welcome)
			else:
			    if cache[sender_id]['purpose'] == "na" and ("job" in message_text or "employment" in message_text):  
			        cache[sender_id]["purpose"] == "job"
			        time.sleep(2)
			        send_quick_reply(sender_id,"Looking for employment services?",job_replies)
			    elif cache[sender_id]['purpose'] = "job":
				if message_text == "Pre-Job Training":
				    send_quick_reply(sender_id, "There are numerous services available. Let's narrow it down.  What is your age group?", age_replies)
			            cache[sender_id]['purpose'] = "PJT"
		    	    	    time.sleep(2)
#		            send_quick_reply(sender_id, "Are you under 30?" + state, youth_replies)	
#			elif cache[sender_id]['state'] == 1 "youth" not in cahce[sender_id].keys():
#			    cache[sender_id]['state'] == 2
#			    log(message_text)
#			    if message_text.lower() == "youth":
#			        cache[sender_id]["youth"] = 1
#				send_quick_reply(sender_id,"What  gender do you identify with?", gender_replies)
#			    elif message_text.lower() == "adult":
#				cache[sender_id]["youth"] = 0
#				send_quick_reply(sender_id,"What  gender do you identify with?", gender_replies)
#			    else:
#				send_message(sender_id, "hmm.. " + state)
#			elif cache[sender_id]['state'] == 2:
#			    cache['sender_id']['state'] == 3
#			    send_message(sender_id,"Are you a member of the First Nations?")	
#			else:
#			    send_message(sender_id,str(cache[sender_id]))
		    except Exception as e:
			send_message(sender_id, "Sorry we are currently experiencing some difficulties, please call 555-555-5555 or email info@tbot.ca")
			log(e.message)
                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200



def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


youth_replies = [
      {
        "content_type":"text",
        "title":"Yes",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED",
 #       "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      },
      {
        "content_type":"text",
        "title":"No",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GREEN",
#        "image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      }
    ]

job_replies = [
      {
        "content_type":"text",
        "title":"Job Finding Services",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED",
       # "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      },
      {
        "content_type":"text",
        "title":"Pre-Job Training",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GREEN",
        #"image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      }
    ]

gender_replies = [
      {
        "content_type":"text",
        "title":"Female",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED",
  #      "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      },
      {
        "content_type":"text",
        "title":"Male",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GREEN",
   #     "image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      },
      {
        "content_type":"text",
        "title":"Other",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED",
    #    "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      }
    ]

language_replies = [
      {
        "content_type":"text",
        "title":"Yes",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED",
      #  "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      },
      {
        "content_type":"text",
        "title":"No",
        "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GREEN",
     #   "image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      }
    ]




def send_quick_reply(recipient_id, message_text,quick_replies):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
             "quick_replies": quick_replies
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
