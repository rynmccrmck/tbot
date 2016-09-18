import os
import sys
import json
import pylru
import time

import requests
from flask import Flask, request

app = Flask(__name__)

size = 1000
cache = pylru.lrucache(size)
wait = 6


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
		        if sender_id not in cache.keys():
			    cache[sender_id] = {"purpose":-1,"youth":-1,"woman":-1}
			    time.sleep(wait)
			    log(cache[sender_id])
                            send_message(sender_id, welcome)
			elif "restart" in message_text or message_text.lower() == "hi" or message_text.lower() == "hello":
			    cache[sender_id] = {"purpose":-1,"youth":-1,"woman":-1,"current":0}
			    time.sleep(wait)
			    log(cache[sender_id])
   			    send_message(sender_id, welcome)
			else:
			    if cache[sender_id]['purpose'] == -1:
				if  ("job" in message_text or "employment" in message_text or "work" in message_text):  
   			            cache[sender_id]['purpose'] = 1
			            time.sleep(wait)
				    log(cache[sender_id])
			            send_quick_reply(sender_id,"Looking for employment services?",job_replies)
				elif "food" in message_text or " eat" in message_text:
				    send_message(sender_id, "placeholder food bank services")
				else:
				    send_message(sender_id, "Sorry I couldn't understand.")
				    log(cache[sender_id])
			    elif cache[sender_id]['purpose'] == 1:
				if "training" in message_text.lower():
			            cache[sender_id]['purpose'] = 2
				    time.sleep(wait)
			            log(cache[sender_id])
				    send_quick_reply(sender_id, "There are numerous services available. Let's narrow it down.  Are you under 30?", youth_replies)
				else:
				    send_message(sender_id,"Job finding placeholder")
				    cache[sender_id]['purpose'] = 3
				    time.sleep(wait)	
		            elif cache[sender_id]['purpose'] == 2 and cache[sender_id]['youth'] == -1:
				if message_text.lower() == "yes":
				    cache[sender_id]['youth'] = 1
				    time.sleep(wait)
				    send_message(sender_id, "Retrieving results, just a moment!")
		                    r = requests.post('http://ec2-52-40-133-183.us-west-2.compute.amazonaws.com:1738/classify', {"data":'{"youth":1}'}) 
				    adrian_data = json.loads("{" + r.json()[1:-1].replace("\n","") + "}")	
				    youth_results(sender_id,"","")
				else:
				    cache[sender_id]['youth'] = 0			
				    time.sleep(wait)
				    send_message(sender_id, "adult placeholder")		
			    else:
				send_message(sender_id,"Sorry I don't understand, are you looking for job services, financial support or something else?")	
				log(cache[sender_id])
		    except Exception as e:
			send_message(sender_id, "Sorry we are currently experiencing some difficulties, please call 555-555-5555 or email info@tbot.ca")
			log(e.message)
			log("done")
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
        "payload":"finding",
       # "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      },
      {
        "content_type":"text",
        "title":"Pre-Job Training",
        "payload":"training",
        #"image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      },
     {
        "content_type":"text",
        "title":"Other",
        "payload":"other",
        #"image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      }
    ]

gender_replies = [
      {
        "content_type":"text",
        "title":"Female",
        "payload":"Female",
  #      "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      },
      {
        "content_type":"text",
        "title":"Male",
        "payload":"Male",
   #     "image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      },
      {
        "content_type":"text",
        "title":"Other",
        "payload":"Other",
    #    "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      }
    ]

language_replies = [
      {
        "content_type":"text",
        "title":"Yes",
        "payload":"Yes",
      #  "image_url":"https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcR5TWbk5DmxpPUfNNCsAxstPfzRm3yJStFx1QC7pvP2wiZ5EmtXDh5Aiw"
      },
      {
        "content_type":"text",
        "title":"No",
        "payload":"No",
     #   "image_url":"https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcSEbkZszcbchKY9Z4gqIX8WFHATnsVNoP-ZdrWYTQ4kIY9vl7Ww"
      }
    ]



def youth_results(recipient_id,message_text, json_data):
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

	"message":{
    "attachment":{
      "type":"template",
      "payload": #{
#        "template_type":"generic",
#        "elements":[
#          {
#            "title":"Welcome to Peter\'s Hats",
#            "item_url":"https://petersfancybrownhats.com",
#            "image_url":"https://petersfancybrownhats.com/company_image.png",
#            "subtitle":"We\'ve got the right hat for everyone.",
#            "buttons":[
#              {
#                "type":"web_url",
#                "url":"https://petersfancybrownhats.com",
#                "title":"View Website"
#              },
 #             {
 #               "type":"postback",
 #               "title":"Start Chatting",
 #               "payload":"DEVELOPER_DEFINED_PAYLOAD"
 #             }              
 #           ]
 #         }
 #       ]
 #     }

{u'template_type': u'generic', u'elements': [{u'buttons': [{u'url': u'www1.toronto.ca/wps/portal/contentonly?vgnextoid=a...', u'type': u'web_url', u'title': u'View Website'}, {u'type': u'phone_number', u'payload': u'+16478875298', u'title': u'Call now'}], u'subtitle': u'full time paid employment preparation program -- 5 week pre-employment including resume preparation, employment readiness skills, career planning, counselling and referral; 16 to 24 week supported', u'item_url': u'www1.toronto.ca/wps/portal/contentonly?vgnextoid=a...', u'image_url': u'https://www.galepartners.com/media/G43_Mugs-12_eAgvk8z.jpg', u'title': u'Toronto. Toronto Youth Job Corps'}, {u'buttons': [{u'url': u'www.yes.on.ca', u'type': u'web_url', u'title': u'View Website'}, {u'type': u'phone_number', u'payload': u'+16478875298', u'title': u'Call now'}], u'subtitle': u'paid, group-based employability and life skills workshops * paid work placements to a maximum of 10 weeks * individual counselling * follow-up support', u'item_url': u'www.yes.on.ca', u'image_url': u'https://www.galepartners.com/media/G43_Mugs-12_eAgvk8z.jpg', u'title': u'Youth Employment Services YES - Youth Job Centre'}, {u'buttons': [{u'url': u'www.covenanthousetoronto.ca', u'type': u'web_url', u'title': u'View Website'}, {u'type': u'phone_number', u'payload': u'+16478875298', u'title': u'Call now'}], u'subtitle': u'', u'item_url': u'www.covenanthousetoronto.ca', u'image_url': u'https://www.galepartners.com/media/G43_Mugs-12_eAgvk8z.jpg', u'title': u'Job Centre'}, {u'buttons': [{u'url': u'www.jobstartworks.org', u'type': u'web_url', u'title': u'View Website'}, {u'type': u'phone_number', u'payload': u'+16478875298', u'title': u'Call now'}], u'subtitle': u'comprehensive employment and job search services * assessment of skills, interests and experience * job search strategies, including resume preparation * information about careers and occupations,', u'item_url': u'www.jobstartworks.org', u'image_url': u'https://www.galepartners.com/media/G43_Mugs-12_eAgvk8z.jpg', u'title': u'JobStart - Lake Shore Boulevard - Ontario Employment Services'}, {u'buttons': [{u'url': u'www.ymcagta.org', u'type': u'web_url', u'title': u'View Website'}, {u'type': u'phone_number', u'payload': u'+16478875298', u'title': u'Call now'}], u'subtitle': u'comprehensive employment and job search services * assessment of skills, interests and experience * job search strategies, including resume preparation * information about careers and occupations,', u'item_url': u'www.ymcagta.org', u'image_url': u'https://www.galepartners.com/media/G43_Mugs-12_eAgvk8z.jpg', u'title': u'YMCA of Greater Toronto - Scarborough North East - Ontario Employment Services'}]}


	}}
	})
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

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
