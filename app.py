# -*- coding: utf-8 -*-
from flask import Flask, Response, request, json, redirect
from flask import make_response
import random
import string
import apiai
import urllib2
import time
import datetime
import requests
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import mysql.connector
from watson_developer_cloud import NaturalLanguageClassifierV1
from watson_developer_cloud import LanguageTranslatorV2 as LanguageTranslator
from twilio.rest import TwilioRestClient
from twilio import twiml
import numpy as np
from watson_developer_cloud import ConversationV1

app = Flask(__name__)

@app.route('/chatalexa', methods=["POST"])
def chatalexa():
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print "hi"
    data = request.data
    event = json.loads(data)
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    print "build_speechlet_response"
    print title
    print output
    print reprompt_text
    print should_end_session
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    print "build_response"
    print speechlet_response
    print session_attributes
    mydata = {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
    return Response(json.dumps(mydata),  mimetype='application/json')
    


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Alexa Skills Kit sample. " \
                    "Please tell me your favorite color by saying, " \
                    "my favorite color is red"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "In correct answer, " \
                    "Please tell me your favorite color"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_favorite_color_attributes(favorite_color):
    return {"favoriteColor": favorite_color}


def LogonSpecificIntent(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """
    print "in"
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False    
    user = session["user"]
    speech_output = ''
    db = mysql.connector.connect(host="59831ab27628e1f85900000d-trialchatbot.rhcloud.com", port=57521, user="adminjuz6bQy", passwd="jSw9dbFyIxtx", db="chatbot")
    cur = db.cursor()
    print user
    if 'accessToken' not in user:
        speech_output = 'Please link your Amazon Account.'
    else:
        accessToken = session['user']['accessToken']
        print accessToken
        if accessToken is None:
            speech_output = 'Please link your Amazon Account.'
        else:
            cur.execute('SELECT count(*) from user where auth_code=%s'%accessToken)
            data = cur.fetchone()
            print data[0]
            if data[0] == 0:
                speech_output = 'Invalid User'
            else:
                if card_title == 'Balance':
                    cur.execute('select ab.available_bal from user u,account_balance ab where ab.olb_id=u.olb_id and ab.acct_type="Checking" and u.auth_code=%s'%accessToken)
                    balance=cur.fetchone()[0]
                    speech_output = 'Checking account balance is $%s'%balance
                elif card_title =='Spent':
                    if 'shop' in intent['slots']:
                        retail = intent['slots']['shop']['value']
                        print retail
                        retailname=[]
                        retailname.append(retail)
                        print retailname
                        string_result = ''                       
                        print string_result
                        for retail1 in retailname: 
                            querystring="'%"+retail1.lower()+"%'"
                            cur.execute('select sum(td.tran_amount) from transaction_details td,user u where td.olb_id=u.olb_id and u.auth_code= %s and td.tran_desc like %s'%(accessToken,querystring))
                            sum_amount=cur.fetchone()[0]
                            print sum_amount
                            if sum_amount is None:
                                sum_amount = 0
                            else:
                                date_format = "%Y-%m-%d"
                                cur.execute('select max(td.date) from transaction_details td,user u where u.olb_id=td.olb_id and u.auth_code = %s and td.tran_desc like %s'%(accessToken,querystring))
                                max_date=cur.fetchone()[0]
                                print max_date
                                cur.execute('select min(td.date) from transaction_details td,user u where u.olb_id=td.olb_id and u.auth_code = %s and td.tran_desc like %s'%(accessToken,querystring))
                                min_date=cur.fetchone()[0]
                                print min_date
                                a = datetime.datetime.strptime(min_date, date_format).date()
                                b = datetime.datetime.strptime(max_date, date_format).date()
                                print a
                                print b
                            string_result += 'You spent $%s on %s between %s and %s.'%(sum_amount,retail1,a,b)
                            print string_result
                        speech_output = string_result
                    else:
                        speech_output = 'Please specify the shop or payment description'
                elif card_title =='Transaction':
                    if 'Number' in intent['slots']:                        
                        if 'value' in intent['slots']['Number']:
                            number = intent['slots']['Number']['value']
                            print number
                            cur.execute('select olb_id from user where auth_code=%s'%accessToken)
                            olb_id=cur.fetchone()[0]
                            cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s LIMIT %s'%(olb_id,number))
                            if cur.fetchall():                                                                                                                                                                        
                                cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s order by td.date desc  LIMIT %s'%(olb_id,number))
                                data=cur.fetchall()
                                print '2'
                                print data
                                string_result = ''
                                count=1
                                for row in data:                                                                                        
                                        sringout= str(row).replace("(", "").replace(")","").split(',')
                                        outstring = '#'
                                        print outstring
                                        outstring += str(count)+" "
                                        for index in range(len(sringout)):                                                                                                
                                                if(index==1):
                                                        tempString = str(sringout[index]).replace("u","").replace("'","").replace(" ", "")
                                                        outstring += " $"+tempString+','
                                                else:
                                                        outstring += str(sringout[index]).replace("u","").replace("'","")+','                                                                                             
                                        print outstring
                                        string_result += outstring
                                        count=count+1
                                print string_result
                                speech_output = string_result                      
                            else:
                                speech_output = 'No transactions.'   
                        else:
                            tran_day=intent['slots']['trans_day']['value']
                            if tran_day is None:
                                speech_output=""
                            else:                                
                                speech_output = "No Transaction Found."
                            
                    else:
                        speech_output = 'Please enter no of transaction.'
                elif card_title =='Bills':
                    if 'Day' in intent['slots']:
                        day=intent['slots']['Day']['value']
                        print day
                        startDate=datetime.datetime.strptime(day, '%Y-%m-%d').strftime('%m/%d/%Y')
                        Date=datetime.datetime.strptime(day, '%Y-%m-%d').strftime('%m/%d/%Y')
                        print Date
                        print startDate
                        cur.execute('select olb_id from user where auth_code=%s'%accessToken)
                        olb_id=cur.fetchone()[0]                                                                                
                        cur.execute('select payment_date,nickname,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                        if cur.fetchall():                                                                                                                                                                        
                                cur.execute('select payment_date,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                data=cur.fetchall()                                                                                
                                string_result = ''                                                                
                                for row in data:                                                                                        
                                        sringout= str(row).replace("(", "").replace(")","").split(',')
                                        outstring = ''
                                        for index in range(len(sringout)):                                                                                                
                                                if(index==2):
                                                        tempString = str(sringout[index]).replace("u","").replace("'","").replace(" ", "")
                                                        outstring += " $"+tempString+','
                                                else:
                                                        outstring += str(sringout[index]).replace("u","").replace("'","")+','                                                                                             
                                        print outstring
                                        string_result += outstring +','
                                cur.execute('select sum(tran_amount) from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                total = cur.fetchone()[0]
                                if total is None:
                                        total=0
                                string_result +='Total due Bill amount is $%s'%total
                                speech_output = string_result
                        else:
                                speech_output = 'No Bills Due.'
                elif card_title =='Dispute':
                    print "inside"
                    account_sid = "ACfaf705ecdfa9632e9d41c3cbdb94a451"
                    auth_token  = "ebddfe1b515e0c3c49e78454f3381d19"
                    client = TwilioRestClient(account_sid, auth_token)
                    cur.execute('select mobile_no from user where auth_code=%s'%accessToken)
                    mobile_num=cur.fetchone()[0]
                    if(mobile_num=='+19193997682'):
                                    mobile_num='+917358384976' 
                    call = client.calls.create(url="http://demo.twilio.com/docs/voice.xml",to=mobile_num,from_="+15084434500")
                    print(call.sid)
                    speech_output="For dispute related queries, support team of customer experience center will contact you shortly."
                elif card_title =='Block':
                    cur.execute('select olb_id from user where auth_code=%s'%accessToken)
                    olb_id=cur.fetchone()[0]
                    print olb_id
                    cur.execute('select card_num from card where olb_id=%s'%olb_id)
                    data=cur.fetchall()
                    print data
                    stringcard='Which Card,'
                    for row in data:
                            card_num=str(row).replace("u","").replace("'","").replace(",","").replace("(","").replace(")","")
                            stringcard+=' '+card_num+' or'                    
                    speech_output=stringcard[:-2]
                    session_attributes.update(create_card_attribute('card'))
                elif card_title =='Visa':
                    card = session['attributes']['card']
                    if card =="card":
                        card_no = intent['slots']['Card_No']['value']
                        speech_output = "Blocked VISA "+card_no+" successfully."
                        session_attributes.update(create_card_attribute(''))                        
                    else:
                        speech_output = "what you want to do with this card."
                elif card_title =='Master':
                    card = session['attributes']['card']
                    if card =="card":
                        card_no = intent['slots']['Card_No']['value']
                        speech_output = "Blocked Master"+card_no+"successfully."
                        session_attributes.update(create_card_attribute(''))                        
                    else:
                        speech_output = "what you want to do with this card."
                                            
    reprompt_text = ""
    db.commit()
    cur.close()
    db.close()
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def create_card_attribute(card):
    return {"card": card}

def general_intent(intent):
    card_title = intent['name']
    print card_title
    session_attributes = {}
    should_end_session = False
    reprompt_text=""
    if card_title == 'Enroll':
        speech_output = 'Enroll to online banking at https://www.newgenbank.com/enroll/olb'
    elif card_title == 'Mortgage':
        speech_output = 'For Fixed 15 years 3.25% and refinance 30 years 4.25%'    
    elif card_title == 'Welcome':
        speech_output = 'Welcome to Bank Alexa Servcice.'
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_color_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']    
    print intent_name
    # Dispatch to your skill's intent handlers
    if (intent_name == "Balance" or intent_name == "Transaction" or intent_name == "Bills" or intent_name == "Spent" or intent_name == "Dispute" or intent_name == "Block" or intent_name == "Visa" or intent_name == "Master"):
        return LogonSpecificIntent(intent, session)
    elif (intent_name == "Enroll" or intent_name == "Mortgage" or intent_name == "Welcome"):
        return general_intent(intent)    
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here
	
@app.route('/ChatBot', methods=['GET'])
def verify():
        token = request.args.get('hub.verify_token')
        if token == "123":
                return request.args.get('hub.challenge')
        else:
                return "error"        


@app.route('/ChatBot', methods=["POST"])
def webhookfb():
        try:
                out_msg = 'How may i help you?'
##                natural_language_classifier = NaturalLanguageClassifierV1(
##                username='7a44b06d-6db7-43c3-bc7a-b50586281336',
##                password='vrN6alai6kaI')
                flag = 'N'
                json_data_final=''               
                ps = PorterStemmer()                
                data = request.data
                dataDict = json.loads(data)                
                print json.dumps(dataDict)
                urld = 'https://tracker.dashbot.io/track?platform=facebook&v=0.8.2-rest&type=incoming&apiKey=N7YXZih9IuRsJikHUotxzbyonxfOE5IHTgtpmeyj'
                headersd = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
                contentsd = json.dumps(dataDict)
                rd = requests.post(urld, data=contentsd, headers=headersd)                
                sender_id= dataDict["entry"][0]["messaging"][0]["sender"]["id"]
                json_data_typing_on={"recipient": {"id": sender_id}, "sender_action": "typing_on"}
                postingMessage(json_data_typing_on);                
                db = mysql.connector.connect(host="59831ab27628e1f85900000d-trialchatbot.rhcloud.com", port=57521, user="adminjuz6bQy", passwd="jSw9dbFyIxtx", db="chatbot")
                cur = db.cursor()
                cur.execute('SELECT count(*) from fb_chatbot where sender_id=%s'%sender_id)
                data = cur.fetchone()
                print data[0]
                if data[0] == 0:
                        cur.execute('insert into fb_chatbot(sender_id) values(%s)'%sender_id)
                cur.execute('SELECT question from fb_chatbot where sender_id=%s'%sender_id)
                question=cur.fetchone()[0]
                cur.execute('SELECT status from fb_chatbot where sender_id=%s'%sender_id)
                status=cur.fetchone()[0]
                postbak_msg = dataDict["entry"][0]["messaging"][0]

                if('message' not in postbak_msg):
                        if('postback' not in postbak_msg):
                                link_status=dataDict["entry"][0]["messaging"][0]["account_linking"]["status"]
                                if(link_status=='linked'):
                                        auth_code=dataDict["entry"][0]["messaging"][0]["account_linking"]["authorization_code"]
                                        cur.execute('update fb_chatbot set auth_code=%s where sender_id=%s',(auth_code,sender_id))
                                        cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                        dataname=cur.fetchone()
                                        print dataname[0]
                                        name = dataname[0]
                                        out_msg = 'Welcome %s'%name
                                elif(link_status=='unlinked'):
                                        cur.execute('update fb_chatbot set auth_code="" where sender_id=%s'%sender_id)
                                        out_msg = 'Logged out successfully'
                        else:
                                if(status=='Y' and question=='BLOCK'):
                                        cardno = dataDict["entry"][0]["messaging"][0]["postback"]["payload"]
                                        cardnumber = "'"+cardno+"'"
                                        cur.execute('update card set card_status="INACTIVE" where card_num=%s'%cardnumber)
                                        cur.execute('update fb_chatbot set status="",question="" where sender_id=%s'%sender_id)
                                        out_msg = 'Card number %s has been blocked successfully'%cardno
                                else:
                                        out_msg=dataDict["entry"][0]["messaging"][0]["postback"]["payload"]
                else:                        
                        msg = dataDict["entry"][0]["messaging"][0]["message"]
                        if 'text' not in msg:
                                type = dataDict["entry"][0]["messaging"][0]["message"]["attachments"][0]["type"]
                                if type =="image":
                                        out_msg = dataDict["entry"][0]["messaging"][0]["message"]["attachments"][0]["payload"]["url"]
                                elif type =="location":
                                        out_msg = dataDict["entry"][0]["messaging"][0]["message"]["attachments"][0]["title"]								                                                       
                        else:
                                txt_msg=dataDict["entry"][0]["messaging"][0]["message"]["text"]                                
##                                classes = natural_language_classifier.classify('8aff06x106-nlc-6768', txt_msg)
##                                watsonDataDict = json.loads(json.dumps(classes, indent=2))
##                                confidence = watsonDataDict["classes"]
##                                for w in confidence:
##                                        if w["class_name"] =='Enroll':
##                                                conf = w["confidence"]
##                                print conf
##                                if conf > 0.9:
##                                        out_msg = 'Enroll to online banking at https://www.newgenbank.com/enroll/olb'
                                words = word_tokenize(txt_msg)
                                tokens = nltk.word_tokenize(txt_msg)
                                tagged = nltk.pos_tag(tokens)
                                entities = nltk.ne_chunk(tagged)
                                print entities
                                for w in words:
                                        if(ps.stem(w).lower()=='enrol'):
                                                if 'online' in str(words).lower() and 'banking' in str(words).lower():                                                
                                                        out_msg = 'Enroll to online banking at https://www.newgenbank.com/enroll/olb'
                                        if(ps.stem(w).lower()=='extern'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():                                                        
                                                        out_string = 'Here are your account balances'+'\n'+'US Bank - '+'\n'
                                                        out_string+= 'Checking Account: $5000'+'\n'+'Savings Account: $2000'+'\n'+'Wells Fargo -'+'\n'
                                                        out_string+= 'Checking Account: $3000'+'\n'+'Savings Account: $1000'
                                                        out_msg = out_string
                                                        break                                                        
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                        if(ps.stem(w).lower()=='insur'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():                                                                                                                
                                                        out_msg='Here are the vehicles that you have with Ameriprise Auto insurance'+'\n'+'Honda City'+'\n'+'Hyundai Elantra'
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                                
                                        if(ps.stem(w).lower()=='appoint'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():
                                                        appointDate = ''
                                                        if 'advisor' in str(words).lower():                                                                
                                                                for subtree in entities.subtrees():
                                                                       for leaves in subtree.leaves():
                                                                               if leaves[1] == 'CD':
                                                                                       appointDate = leaves[0]
                                                                                       break
                                                                if appointDate:
                                                                        out_msg = 'Sure, I have setup an appointment with your advisor Bill for %s'%appointDate
                                                                else:
                                                                        out_msg='Please specify the date.'
                                                                break                                                        
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                        if(ps.stem(w).lower()=='login'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)                                                
                                                if cur.fetchone():                                                        
                                                        out_msg='You already logged into the account.'                                                        
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                                        
                                        if(ps.stem(w).lower()=='log'):
                                                if 'me' in str(words).lower() and 'out' in str(words).lower():
                                                        cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)                                                
                                                        if cur.fetchone():
                                                                flag='Y'
                                                                json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "Logout","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_unlink"}]}]}}}}                                                                                                                                                                                                                
                                                        else:
                                                                out_msg='You already logged out the account.'
                                        if(ps.stem(w).lower()=='pay'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():
                                                        person_name=''
                                                        amount=''
                                                        for subtree in entities.subtrees():                                                                
                                                                if subtree.label() == 'PERSON':                                                                
                                                                        person_name = "'"+subtree.leaves()[0][0]+"'"
                                                                for leaves in subtree.leaves():                                                                        
                                                                        if leaves[1] == 'CD':
                                                                                amount = leaves[0]
                                                                if person_name:
                                                                        if amount:
                                                                                cur.execute('select u.olb_id from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                                                olb_id=cur.fetchone()[0]
                                                                                print 'olb_id%s'%olb_id
                                                                                print 'name%s'%person_name                                                                                
                                                                                cur.execute('select payee_id from payee_details where nickname=%s and olb_id=%s'%(person_name,olb_id))
                                                                                if cur.fetchone():                                                                                                                                                                        
                                                                                        cur.execute('select payee_id from payee_details where nickname=%s'%person_name)
                                                                                        payee_id=cur.fetchone()[0]
                                                                                        cur.execute('select p2p_email_id from payee_details where nickname=%s'%person_name)
                                                                                        email_id=cur.fetchone()[0]
                                                                                        print 'payee id%s'%payee_id
                                                                                        cur.execute('insert into transaction_details values(%s,"231456",%s,"Payment",%s,%s)'%(olb_id,"'"+time.strftime('%Y-%m-%d')+"'",amount,payee_id))
                                                                                        cur.execute('update fb_chatbot set status="Y",question="OTP" where sender_id=%s'%sender_id)
                                                                                        out_msg = 'Please enter a OTP sent to your mobile'
                                                                                else:
                                                                                        out_msg = 'Payee nickname not found.'

                                                                        else:
                                                                                out_msg = 'Please enter a amount'   
                                                                else:                                                                                                                                        
                                                                        out_msg = 'Please enter a payee name'                                                               
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                        if(ps.stem(w).lower()=='transact'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():
                                                        number=''                                                        
                                                        for subtree in entities.subtrees():                                                                                                                                
                                                                for leaves in subtree.leaves():                                                                        
                                                                        if leaves[1] == 'CD':
                                                                                number = leaves[0]
                                                                print 'Nu,ber%s'%number
                                                                cur.execute('select u.olb_id from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                                olb_id=cur.fetchone()[0]
                                                                if number:
                                                                        print '1'
                                                                        cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s LIMIT %s'%(olb_id,number))
                                                                        if cur.fetchall():                                                                                                                                                                        
                                                                                cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s order by td.date desc  LIMIT %s'%(olb_id,number))
                                                                                data=cur.fetchall()
                                                                                print '2'
                                                                                print data
                                                                                string_result = ''
                                                                                string_result +='Date   Amount  Description'+'\n'
                                                                                for row in data:                                                                                        
                                                                                        sringout= str(row).replace("(", "").replace(")","").split(',')
                                                                                        outstring = ''
                                                                                        for index in range(len(sringout)):                                                                                                
                                                                                                if(index==1):
                                                                                                        tempString = str(sringout[index]).replace("u","").replace("'","").replace(" ", "")
                                                                                                        outstring += " $"+tempString
                                                                                                else:
                                                                                                        outstring += str(sringout[index]).replace("u","").replace("'","")                                                                                             
                                                                                        print outstring
                                                                                        string_result += outstring + '\n'                                                                                                                                                                        
                                                                                print string_result
                                                                                out_msg = string_result
                                                                        else:
                                                                                out_msg = 'No transactions.'

                                                                else:
                                                                        out_msg = 'Please enter a no of transactions'                                                                                                                           
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                        if(ps.stem(w).lower()=='bill'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():
                                                        startDate=time.strftime("%m/%d/%Y")
                                                        Date=time.strftime("%m/%d/%Y")
                                                        if 'today' in str(words).lower():
                                                                Date=Date
                                                        elif('tomorrow' in str(words).lower()):
                                                                Date=datetime.datetime.strptime(Date, "%m/%d/%Y")
                                                                tempDate = Date + datetime.timedelta(days=1)
                                                                Date =  tempDate.strftime('%m/%d/%Y')
                                                                startDate = tempDate.strftime('%m/%d/%Y')
                                                        else:
                                                                if 'next' in str(words).lower():
                                                                        Date=datetime.datetime.strptime(Date, "%m/%d/%Y")
                                                                        startDate = Date + datetime.timedelta(days=7)
                                                                        startDate = startDate.strftime('%m/%d/%Y')
                                                                        tempDate = Date + datetime.timedelta(days=14)
                                                                else:                                                                        
                                                                        Date=datetime.datetime.strptime(Date, "%m/%d/%Y")
                                                                        tempDate = Date + datetime.timedelta(days=7)
                                                                Date =  tempDate.strftime('%m/%d/%Y')
                                                                for subtree in entities.subtrees():
                                                                       for leaves in subtree.leaves():
                                                                               if leaves[1] == 'CD':
                                                                                       startDate = leaves[0]
                                                                                       Date = leaves[0]                                    
                                                        print Date
                                                        print startDate
                                                        cur.execute('select u.olb_id from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                        olb_id=cur.fetchone()[0]                                                        
                                                        print '1'
                                                        cur.execute('select payment_date,nickname,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                                        if cur.fetchall():                                                                                                                                                                        
                                                                cur.execute('select payment_date,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                                                data=cur.fetchall()                                                                                
                                                                string_result = ''                                                                
                                                                for row in data:                                                                                        
                                                                        sringout= str(row).replace("(", "").replace(")","").split(',')
                                                                        outstring = ''
                                                                        for index in range(len(sringout)):                                                                                                
                                                                                if(index==2):
                                                                                        tempString = str(sringout[index]).replace("u","").replace("'","").replace(" ", "")
                                                                                        outstring += " $"+tempString
                                                                                else:
                                                                                        outstring += str(sringout[index]).replace("u","").replace("'","")                                                                                             
                                                                        print outstring
                                                                        string_result += outstring + '\n'
                                                                cur.execute('select sum(tran_amount) from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                                                total = cur.fetchone()[0]
                                                                if total is None:
                                                                        total=0
                                                                string_result +='Total due Bill amount is $%s'%total
                                                                out_msg = string_result
                                                        else:
                                                                out_msg = 'No Bills Due.'                                                                                                                                                                                        
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                        if(ps.stem(w).lower()=='balanc'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():                                                        
                                                        cur.execute('select ab.available_bal from user u,fb_chatbot fb,account_balance ab where ab.olb_id=u.olb_id and u.auth_code=fb.auth_code and ab.acct_type="Checking" and fb.sender_id=%s'%sender_id)
                                                        balance=cur.fetchone()[0]
                                                        out_msg = 'Checking account balance is $%s'%balance
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}                                                        

                                        if(ps.stem(w).lower()=='spent'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)                                                
                                                if cur.fetchone():
                                                        cur.execute('select u.olb_id from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                        olb_id=cur.fetchone()[0]
                                                        descstring = []
                                                        string_result = ''
                                                        string_result +='Please find the below details'+'\n\n'
                                                        for subtree in entities.subtrees():
                                                                for leaves in subtree.leaves():
                                                                        if leaves[1] == 'NNP':
                                                                                descstring.append(leaves[0])
                                                                break
                                                        if not descstring:
                                                                out_msg = 'Please specify the shop or payment description'
                                                        else:
                                                                for desc in descstring: 
                                                                        querystring="'%"+desc.lower()+"%'"
                                                                        cur.execute('select sum(tran_amount) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                                                        balance=cur.fetchone()[0]
                                                                        if balance is None:
                                                                                balance = 0
                                                                        else:
                                                                                date_format = "%Y-%m-%d"
                                                                                cur.execute('select max(date) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                                                                max_date=cur.fetchone()[0]
                                                                                cur.execute('select min(date) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                                                                min_date=cur.fetchone()[0]
                                                                                a = datetime.datetime.strptime(min_date, date_format).date()
                                                                                b = datetime.datetime.strptime(max_date, date_format).date()
                                                                                delta = b - a                                                                                
                                                                        string_result += 'You spent $%s on %s between %s and %s.'%(balance,desc,a,b)+'\n'
                                                                out_msg = string_result
                                                else:                                                        
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}                                                                                                                
                                        if(ps.stem(w).lower()=='weekend'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)                                                
                                                if cur.fetchone():
                                                        cur.execute('select u.olb_id from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                        olb_id=cur.fetchone()[0]                                                                                                        
                                                        cur.execute('select tran_amount from transaction_details where olb_id = %s'%(olb_id))
                                                        balance=cur.fetchall()
                                                        #date = [1,2,3,4]
                                                        #amount = [12,120,230,240]
                                                        #lr = LinearRegression()
                                                        #lr.fit(date,amount)
                                                        #b_0   = lr.intercept_
                                                        #coeff = lr.coef_
                                                        #pred = lr.predict(1)
                                                        #print pred
                                                        print balance.replace("(", "").replace(")","").split(',')
                                                        out_msg = 'You might need $%s based on your past history.'%(balance)                                                       
                                                else:                                                        
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}                                                        
                                        if(ps.stem(w).lower()== 'atm'):
                                                for subtree in entities.subtrees():
                                                        if subtree.label() == 'GPE':
                                                                print subtree.label()
                                                                print "if"
                                                                location = subtree.leaves()[0][0]
                                                                if(location.lower()=="raleigh"):
                                                                        flag='Y'
                                                                        json_data_final={"recipient": {"id": sender_id}, "message":{"attachment": {"type": "template", "payload": {"template_type":"button","text":"List Of ATM's in Raleigh","buttons":[{"type":"web_url","url":"http://maps.google.com/?q=35.785878,-78.661062","title":"Oberlin Road"},{"type":"web_url","url":"http://maps.google.com/?q=35.836635,-78.645072","title":"North Hills"},{"type":"web_url","url":"http://maps.google.com/?q=35.805156,-78.647335","title":"Fairview Road"}]}}}}
                                                                else:
                                                                        out_msg="We don't have any ATM'S in this loaction."   
                                                        else:
                                                                print "else"
                                                                cur.execute('update fb_chatbot set status="Y",question="LOCATION" where sender_id=%s'%sender_id)
                                                                out_msg="Please enter a location."
                                        if(ps.stem(w).lower()== 'help'):
                                                out_msg='We understand below list of questions:'+'\n'+'List of ATM' + '\n' +'What is Balance'+'\n'+'Last n transactions'+'\n'+'Block the card'+'\n'+'How much i spent on any retail name'+'\n'+'Bills due'
                                        if(ps.stem(w).lower()== 'disput'):
                                                account_sid = "ACfaf705ecdfa9632e9d41c3cbdb94a451"
                                                auth_token  = "ebddfe1b515e0c3c49e78454f3381d19"
                                                client = TwilioRestClient(account_sid, auth_token)
                                                cur.execute('select u.mobile_no from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                mobile_num=cur.fetchone()[0]
                                                if(mobile_num=='+19193997682'):
                                                        mobile_num='+917358384976' 
                                                call = client.calls.create(url="http://demo.twilio.com/docs/voice.xml",to=mobile_num,from_="+15084434500")
                                                print(call.sid)
                                                out_msg="For dispute related queries, support team of customer experience center will contact you shortly."
                                        if(ps.stem(w).lower()=='block'):
                                                cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                if cur.fetchone():
                                                        cur.execute('select u.olb_id from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                                        olb_id=cur.fetchone()[0]
                                                        print olb_id
                                                        cur.execute('select card_num from card where olb_id=%s'%olb_id)
                                                        data=cur.fetchall()
                                                        print data
                                                        stringcard=''
                                                        stringcard+='{"recipient": {"id": '+sender_id+'}, "message":{"attachment": {"type": "template", "payload": {"template_type":"button","text":"Please choose the card","buttons":['
                                                        for row in data:
                                                                card_num=str(row).replace("u","").replace("'","").replace(",","").replace("(","").replace(")","")
                                                                stringcard+='{"type":"postback","title":"'+card_num+'","payload":"'+card_num+'"},'
                                                        finalstr=stringcard[:-1]                                                             
                                                        finalstr+=']}}}}'
                                                        print finalstr
                                                        flag='Y'
                                                        json_data_final=json.loads(finalstr)
                                                        cur.execute('update fb_chatbot set status="Y",question="BLOCK" where sender_id=%s'%sender_id)
                                                else:
                                                        flag='Y'
                                                        json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing client, please logon for bot banking.","image_url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/images/bank-logo.png","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                                
                                if(status=="Y" and question=="LOCATION"):
                                        for subtree in entities.subtrees():
                                                if subtree.label() == 'GPE':
                                                        print subtree.label()
                                                        location = subtree.leaves()[0][0]                                                
                                                        if(location.lower()=="raleigh"):
                                                                out_msg="ATM list in Raleigh"
                                                                flag='Y'
                                                                json_data_final={"recipient": {"id": sender_id}, "message":{"attachment": {"type": "template", "payload": {"template_type":"button","text":"List Of ATM's in Raleigh","buttons":[{"type":"web_url","url":"http://maps.google.com/?q=35.785878,-78.661062","title":"Oberlin Road"},{"type":"web_url","url":"http://maps.google.com/?q=35.836635,-78.645072","title":"North Hills"},{"type":"web_url","url":"http://maps.google.com/?q=35.805156,-78.647335","title":"Fairview Road"}]}}}}
                                                        else:
                                                                out_msg="We don't have any ATM'S in this loaction."   
                                                        cur.execute('update fb_chatbot set status="",question="" where sender_id=%s'%sender_id)
                                if(status=="Y" and question=="OTP"):
                                        cur.execute('select p2p_email_id from payee_details where nickname="John"')
                                        email_id=cur.fetchone()[0]
                                        out_msg = 'Payment completed successfully to %s'%email_id
                                        cur.execute('update fb_chatbot set status="",question="" where sender_id=%s'%sender_id)         
                print "sender id %s" %sender_id
                json_data_typing_off={"recipient": {"id": sender_id}, "sender_action": "typing_off"}
                postingMessage(json_data_typing_off);
                if(flag=='N'):
                        json_data_final={"recipient": {"id": sender_id}, "message": {"text": out_msg}}
                                      
                postingMessage(json_data_final);
                mid=''
                postbak_msg = dataDict["entry"][0]["messaging"][0]
                if ('message' not in postbak_msg):
                        mid=''
                else:
                        mid=dataDict["entry"][0]["messaging"][0]["message"]["mid"]
                
                urldr = 'https://tracker.dashbot.io/track?platform=facebook&v=0.8.2-rest&type=outgoing&apiKey=N7YXZih9IuRsJikHUotxzbyonxfOE5IHTgtpmeyj'
                headersdr = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
                contentsdr = json.dumps({'qs':{'access_token': 'EAAWZA5iaZAErIBAAMnGkbZCDQyQJSHFqls0sVshQrRrPtBCoARBiJj5cZA7OxHwGbJjR9IBgdB3c84UaIBPDTbR7LAWGnbfmMYqUX09duaO5hKlTyrXN1h5NEwqtpR0ijIKXlCrjP4adQRAL8ZA91LJ8iYZB9GwpZAItsyOQqkvTgZDZD'},'uri':'https://graph.facebook.com/v2.6/me/messages','json':json_data_final,'method': 'POST','responseBody':{'recipient_id': sender_id,'message_id': mid}})                
                rdr = requests.post(urldr, data=contentsdr, headers=headersdr) 
                
                db.commit()
                cur.close()
                db.close()
        except Exception as e:
                print(str(e))
        return "ok"

@app.route('/TapcoBot', methods=['GET'])
def tapcoverify():
        token = request.args.get('hub.verify_token')
        if token == "123":
                return request.args.get('hub.challenge')
        else:
                return "error"

@app.route('/TapcoBot', methods=["POST"])
def tapcowebhookfb():
        try:
                out_msg = 'How may i help you?'                        
                data = request.data
                dataDict = json.loads(data)
                flag='N'
                print json.dumps(dataDict)
                urld = 'https://tracker.dashbot.io/track?platform=facebook&v=0.8.2-rest&type=incoming&apiKey=uPoJIxa0sbI3G7hCQoqiTFOgeJzXTJFTitQkJpB1'
                headersd = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
                contentsd = json.dumps(dataDict)
                rd = requests.post(urld, data=contentsd, headers=headersd)
                sender_id= dataDict["entry"][0]["messaging"][0]["sender"]["id"]
                json_data_typing_on={"recipient": {"id": sender_id}, "sender_action": "typing_on"}
                postingMessageTapco(json_data_typing_on);
                db = mysql.connector.connect(host="59831ab27628e1f85900000d-trialchatbot.rhcloud.com", port=57521, user="adminjuz6bQy", passwd="jSw9dbFyIxtx", db="chatbot")
                cur = db.cursor()
                cur.execute('SELECT count(*) from fb_chatbot where sender_id=%s'%sender_id)
                data = cur.fetchone()
                print data[0]
                if data[0] == 0:
                        cur.execute('insert into fb_chatbot(sender_id) values(%s)'%sender_id)
                postbak_msg = dataDict["entry"][0]["messaging"][0]

                if('message' not in postbak_msg):
                        if('postback' not in postbak_msg):
                                link_status=dataDict["entry"][0]["messaging"][0]["account_linking"]["status"]
                                if(link_status=='linked'):
                                        auth_code=dataDict["entry"][0]["messaging"][0]["account_linking"]["authorization_code"]
                                        cur.execute('update fb_chatbot set auth_code=%s where sender_id=%s',(auth_code,sender_id))
                                        cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                        dataname=cur.fetchone()
                                        print dataname[0]
                                        name = dataname[0]
                                        out_msg = 'Welcome %s'%name
                                elif(link_status=='unlinked'):
                                        cur.execute('update fb_chatbot set auth_code="" where sender_id=%s'%sender_id)
                                        out_msg = 'Logged out successfully'                      
                else:                        
                        msg = dataDict["entry"][0]["messaging"][0]["message"]
                        if 'text' not in msg:
                                type = dataDict["entry"][0]["messaging"][0]["message"]["attachments"][0]["type"]
                                if type =="image":
                                        out_msg = dataDict["entry"][0]["messaging"][0]["message"]["attachments"][0]["payload"]["url"]
                                elif type =="location":
                                        out_msg = dataDict["entry"][0]["messaging"][0]["message"]["attachments"][0]["title"]								                                                       
                        else:
                                txt_msg=dataDict["entry"][0]["messaging"][0]["message"]["text"]
                                if(txt_msg.lower() =='log out'):                                                
                                        cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)                                                
                                        if cur.fetchone():
                                                flag='Y'
                                                json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "Logout","image_url": "","buttons": [{"type": "account_unlink"}]}]}}}} 
                                        else:
                                                out_msg='You already logged out the account.'
                                elif("broker" in txt_msg.lower()):
                                        out_msg='Please visit the below url for more information'+'\n'+'https://www.newgenbank.com/mga/broker'
                                elif("catalog" in txt_msg.lower()):
                                        flag='Y'
                                        json_data_final={"recipient":{ "id":sender_id},"message":{"attachment":{"type":"template","payload":{"template_type":"button","text":"Please find the below product catalog.","buttons":[{"type":"web_url","url":"https://google.com","title":"Builders Risk"},{"type":"web_url","url":"https://google.com","title":"Personal Liability"},{"type":"web_url","url":"https://google.com","title":"Contractor"}]}}}}
                                else:
                                        cur.execute('select u.username from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                        if cur.fetchone():
                                                if txt_msg.lower() == 'hola':
                                                        out_msg='Gracias por ponerse en contacto con NewGen. ¿Con qué puedo ayudarte? Algunas cosas que usted puede preguntarme: La cotización del dueño de una casa nueva, encuadernar una cotización, informar una nueva reclamación, el estado en mi demanda etc.'
                                                else:
                                                        ai = apiai.ApiAI('9ad560fb862e41f8a1b8c55ca5ea2ff0')
                                                        requ = ai.text_request()
                                                        requ.lang = 'en'  # optional, default value equal 'en'
                                                        requ.session_id = sender_id
                                                        requ.query = txt_msg
                                                        respo = requ.getresponse()
                                                        #print (response.read())
                                                        out_resp= json.loads(respo.read())
                                                        print out_resp
                                                        speech = out_resp["result"]["fulfillment"]["speech"]
                                                        print speech
                                                        
                                                        if "Your quote id" in speech:
                                                                out_msg= out_resp["result"]["fulfillment"]["speech"]
                                                                json_data_final={"recipient": {"id": sender_id}, "message": {"text": out_msg}}
                                                                postingMessageTapco(json_data_final);
                                                                flag='Y'
                                                                json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "file","payload": {"url":"https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/resources/pdf/Quote_Details.pdf" }}}}
                                                        out_msg= out_resp["result"]["fulfillment"]["speech"]
                                        else:
                                                flag='Y'
                                                json_data_final={"recipient":{"id":sender_id},"message": {"attachment": {"type": "template","payload": {"template_type": "generic","elements": [{"title": "If you are an existing agent, please logon for MGA bot.","image_url": "","buttons": [{"type": "account_link","url": "https://chatbot-trialchatbot.rhcloud.com/SpringMVCloginExample/login"}]}]}}}}
                                        
                                                                        
                print "sender id %s" %sender_id                
                json_data_typing_off={"recipient": {"id": sender_id}, "sender_action": "typing_off"}
                postingMessageTapco(json_data_typing_off);
                if(flag=='N'):
                        json_data_final={"recipient": {"id": sender_id}, "message": {"text": out_msg}}
                                      
                postingMessageTapco(json_data_final);
                mid=''
                postbak_msg = dataDict["entry"][0]["messaging"][0]
                if ('message' not in postbak_msg):
                        mid=''
                else:
                        mid=dataDict["entry"][0]["messaging"][0]["message"]["mid"]
                
                urldr = 'https://tracker.dashbot.io/track?platform=facebook&v=0.8.2-rest&type=outgoing&apiKey=uPoJIxa0sbI3G7hCQoqiTFOgeJzXTJFTitQkJpB1'
                headersdr = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
                contentsdr = json.dumps({'qs':{'access_token': 'EAAWZA5iaZAErIBAAMnGkbZCDQyQJSHFqls0sVshQrRrPtBCoARBiJj5cZA7OxHwGbJjR9IBgdB3c84UaIBPDTbR7LAWGnbfmMYqUX09duaO5hKlTyrXN1h5NEwqtpR0ijIKXlCrjP4adQRAL8ZA91LJ8iYZB9GwpZAItsyOQqkvTgZDZD'},'uri':'https://graph.facebook.com/v2.6/me/messages','json':json_data_final,'method': 'POST','responseBody':{'recipient_id': sender_id,'message_id': mid}})                
                rdr = requests.post(urldr, data=contentsdr, headers=headersdr) 
                db.commit()
                cur.close()
                db.close()
             
        except Exception as e:
                print(str(e))
        return "ok"        

def postingMessage(json_data):
        req = urllib2.Request('https://graph.facebook.com/v2.6/me/messages?access_token=EAAWZA5iaZAErIBAAMnGkbZCDQyQJSHFqls0sVshQrRrPtBCoARBiJj5cZA7OxHwGbJjR9IBgdB3c84UaIBPDTbR7LAWGnbfmMYqUX09duaO5hKlTyrXN1h5NEwqtpR0ijIKXlCrjP4adQRAL8ZA91LJ8iYZB9GwpZAItsyOQqkvTgZDZD')
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(json_data))
        return response;

def postingMessageTapco(json_data):
        req = urllib2.Request('https://graph.facebook.com/v2.6/me/messages?access_token=EAAC5jeldkOgBANCAQg9HoZAIu5THZAWzFcxMyY7FmYmZBYL1PcriZAoqdKN8HM87pTYRizjfAZBlaAvxXe5MqJTxCR8cu3vMEdW8ZBAWo5B9U3fUCwY6wrfxUHgRGvJVW6OVl6ZB8E8eZCKmJM7LvyJZCotRFKfA3avdVE6FHdlgsMgZDZD')
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(json_data))
        return response;

@app.route("/sms", methods=['GET', 'POST'])
def incoming_sms():
        """Send a dynamic reply to an incoming text message"""
        out_msg='How may i help you?'
        natural_language_classifier = NaturalLanguageClassifierV1(
        username='7a44b06d-6db7-43c3-bc7a-b50586281336',
        password='vrN6alai6kaI')
        ps = PorterStemmer()
        db = mysql.connector.connect(host="59831ab27628e1f85900000d-trialchatbot.rhcloud.com", port=57521, user="adminjuz6bQy", passwd="jSw9dbFyIxtx", db="chatbot")
        cur = db.cursor()
        txt_msg=request.values.get('Body', None).encode('utf-8')
        from_number=request.values.get('From', None)
        print txt_msg
        print from_number
        if not from_number:
                from_number='23'		
        print from_number
        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
        if cur.fetchone():                              
                print "before"
                conversation = ConversationV1(
                        username='fae8a157-a382-43e2-bddb-59ef82946481',
                        password='mdqboUrRRbyO',
                        version='2016-09-20'
                )
               
                cur.execute('select context from user where mobile_no=%s'%from_number)
                if cur.fetchone()[0]:
                        cur.execute('select context from user where mobile_no=%s'%from_number)
                        context= json.loads(cur.fetchone()[0])
                else:
                        context={}   
                        
                
                print context
                language_translator = LanguageTranslator(
                        username='8994c77f-8245-4ca6-b7c9-adb32e44f6f4',
                        password='SPZZy6ybfzGb')

                language = language_translator.identify(txt_msg)                
                watsonDataDict = json.loads(json.dumps(language, indent=2))
                confidence1 = watsonDataDict["languages"][0]
                language_val1=confidence1["language"]
                confidence2 = watsonDataDict["languages"][1]
                language_val2=confidence2["language"]
                
                print language_val1
                print language_val2
                workspace_id='04c1f7c2-c655-46f8-9527-809809fc4282'
                if language_val1 == 'es' or language_val2== 'es':                        
                        workspace_id = 'b9757313-7979-48d7-88ac-e33241397980'
                
                
                

                response = conversation.message(
                        workspace_id=workspace_id,
                        message_input={'text': txt_msg},
                        context=context
                )
                
                dataDict = json.loads(json.dumps(response))        
                fetcontext = json.dumps(dataDict["context"])
                fetcontext1 = "'"+fetcontext+"'"
                print fetcontext1
                cur.execute('update user set context=%s where mobile_no=%s'%(fetcontext1,from_number))
                out_msg= dataDict["output"]["text"][0]
                action=dataDict["output"]["action"]
                print action
                if action =='list':
                        account_list="\n"+"1-Checking 4954"+"\n"+"2-Savings 1256"+"\n"+"3-Creditcard 2572"
                        out_msg=out_msg%account_list
                elif action == 'list_spanish':
                        account_list="\n"+"uno-Checking 4954"+"\n"+"dos-Savings 1256"+"\n"+"Tres-Creditcard 2572"
                        out_msg=out_msg%account_list
                elif action == 'final':
                        acct_index= dataDict["context"]["acct_index"]
                        print acct_index
                        acct=''
                        bal=''
                        if acct_index == 1:
                                acct="Checking 4954"
                                bal="$1232"
                        if acct_index ==2:
                                acct="Saving 1256"
                                bal="$1000"
                        if acct_index == 3:
                                acct="Creditcard 2572"
                                bal="$10000"
                        out_msg=out_msg%(acct,bal)
                elif action == 'final_spanish':
                        acct_index= dataDict["context"]["acct_index"]
                        print acct_index
                        acct=''
                        bal=''
                        if acct_index == 'uno':
                                acct="Checking 4954"
                                bal="$1232"
                        if acct_index =='dos':
                                acct="Saving 1256"
                                bal="$1000"
                        if acct_index == 'Tres':
                                acct="Creditcard 2572"
                                bal="$10000"
                        out_msg=out_msg%(acct,bal)
                elif action == 'balance':
                        cur.execute('select ab.available_bal from user u,account_balance ab where ab.olb_id=u.olb_id and ab.acct_type="Checking" and u.mobile_no=%s'%from_number)
                        balance=cur.fetchone()[0]
                        out_msg = 'Checking account balance is $%s'%balance
                elif action == 'interest':
                        int_year=''
                        int_type=''
                        entities= dataDict["entities"]
                        if entities:                        
                                for ent in entities:
                                    if ent["entity"] == 'Interest_Year':
                                        int_year = ent["value"]
                                    if ent["entity"] == 'Mortgage_Type':
                                        int_type = ent["value"]
                        if int_year=='15 years' and int_type == 'fixed':
                                rate='3.25%'
                                out_msg=out_msg%rate
                        if int_year=='30 years' and int_type == 'refinance':
                                rate='4.25%'
                                out_msg=out_msg%rate
                elif action == 'transaction':
                        entities= dataDict["entities"]                
                        if entities:
                                number=''
                                for ent in entities:
                                    if ent["entity"] == 'sys-number':
                                        number = ent["value"]
                        print number
                        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
                        olb_id=cur.fetchone()[0]
                        print olb_id
                        if number:                        
                                cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s LIMIT %s'%(olb_id,number))
                                if cur.fetchall():                                                                                                                                                                        
                                        cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s order by td.date desc  LIMIT %s'%(olb_id,number))
                                        data=cur.fetchall()
                                        print data
                                        string_result = ''
                                        string_result +='Date   Amount  Description'+'\n'
                                        for row in data:                                                                                        
                                                sringout= str(row).replace("(", "").replace(")","").split(',')
                                                outstring = ''
                                                for index in range(len(sringout)):                                                                                                
                                                        if(index==1):
                                                                tempString = str(sringout[index]).replace("u","").replace("'","").replace(" ", "")
                                                                outstring += " $"+tempString
                                                        else:
                                                                outstring += str(sringout[index]).replace("u","").replace("'","")                                                                                             
                                                print outstring
                                                string_result += outstring + '\n'                                                                                                                                                                        
                                        print string_result
                                        out_msg = out_msg%string_result
                elif action == 'bill':
                        entities= dataDict["entities"]
                        period=''
                        print "23"
                        if entities:                        
                                for ent in entities:
                                    if ent["entity"] == 'period':
                                        period = ent["value"]
                        startDate=time.strftime("%m/%d/%Y")
                        Date=time.strftime("%m/%d/%Y")
                        if period == 'today':
                                Date=Date
                        elif period == 'tomorrow':
                                Date=datetime.datetime.strptime(Date, "%m/%d/%Y")
                                tempDate = Date + datetime.timedelta(days=1)
                                Date =  tempDate.strftime('%m/%d/%Y')
                                startDate = tempDate.strftime('%m/%d/%Y')
                        else:
                                print "else"
                                Date=datetime.datetime.strptime(Date, "%m/%d/%Y")
                                tempDate = Date + datetime.timedelta(days=7)
                                Date =  tempDate.strftime('%m/%d/%Y')                                                        
                        print Date
                        print startDate
                        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
                        olb_id=cur.fetchone()[0]                                                        
                        print '1'
                        cur.execute('select payment_date,nickname,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                        if cur.fetchall():                                                                                                                                                                        
                                cur.execute('select payment_date,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                data=cur.fetchall()                                                                                                        
                                cur.execute('select sum(tran_amount) from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                total = cur.fetchone()[0]
                                if total is None:
                                        total=0                        
                                out_msg = out_msg%total
                        else:
                                out_msg = 'No Bills Due.'
                elif action == 'spent':
                        entities= dataDict["entities"]
                        retailname=[]
                        print "23"
                        if entities:                        
                                for ent in entities:
                                    if ent["entity"] == 'retail_name':
                                        retailname.append(ent["value"])
                        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
                        olb_id=cur.fetchone()[0]
                        
                        string_result = ''
                        string_result +='Please find the below details'+'\n\n'
                        
                        if not retailname:
                                out_msg = 'Please specify the shop or payment description'
                        else:
                                for desc in retailname: 
                                        querystring="'%"+desc.lower()+"%'"
                                        cur.execute('select sum(tran_amount) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                        balance=cur.fetchone()[0]
                                        if balance is None:
                                                balance = 0
                                        else:
                                                date_format = "%Y-%m-%d"
                                                cur.execute('select max(date) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                                max_date=cur.fetchone()[0]
                                                cur.execute('select min(date) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                                min_date=cur.fetchone()[0]
                                                a = datetime.datetime.strptime(min_date, date_format).date()
                                                b = datetime.datetime.strptime(max_date, date_format).date()
                                                delta = b - a                                                                                
                                        string_result += 'You spent $%s on %s between %s and %s.'%(balance,desc,a,b)+'\n'
                                out_msg = string_result
                elif action == 'dispute':
                        account_sid = "ACfaf705ecdfa9632e9d41c3cbdb94a451"
                        auth_token  = "ebddfe1b515e0c3c49e78454f3381d19"
                        client = TwilioRestClient(account_sid, auth_token)
                        cur.execute('select mobile_no from user where mobile_no=%s'%from_number)
                        mobile_num=cur.fetchone()[0]
                        if(mobile_num=='+19193997682'):
                                        mobile_num='+917358384976' 
                        call = client.calls.create(url="http://demo.twilio.com/docs/voice.xml",to=mobile_num,from_="+15084434500")
                        print(call.sid)
                        out_msg="For dispute related queries, support team of customer experience center will contact you shortly."
        else:
                print 'else'
                out_msg='No user with this mobile number enrolled'
                 
                                                    
        print out_msg
        # Start our TwiML response
        resp = twiml.Response()
        db.commit()
        cur.close()
        db.close()
        resp.message(out_msg)
   

        return str(resp)

@app.route("/apiai", methods=['GET', 'POST'])
def chatapiai():
        """Send a dynamic reply to an incoming text message"""
        out_msg='How may i help you?'
        natural_language_classifier = NaturalLanguageClassifierV1(
        username='7a44b06d-6db7-43c3-bc7a-b50586281336',
        password='vrN6alai6kaI')
        ps = PorterStemmer()
        db = mysql.connector.connect(host="59831ab27628e1f85900000d-trialchatbot.rhcloud.com", port=57521, user="adminjuz6bQy", passwd="jSw9dbFyIxtx", db="chatbot")
        cur = db.cursor()
        txt_msg=request.values.get('Body', None).encode('utf-8')
        from_number=request.values.get('From', None)
        print txt_msg
        print from_number
        if not from_number:
                from_number='23'
        print from_number
        cur.execute('select mobile_no from user where auth_code=%s'%from_number)
        from_number = cur.fetchone()[0]
        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
        if cur.fetchone():                              
                print "before"
                conversation = ConversationV1(
                        username='fae8a157-a382-43e2-bddb-59ef82946481',
                        password='mdqboUrRRbyO',
                        version='2016-09-20'
                )
               
                cur.execute('select context from user where mobile_no=%s'%from_number)
                if cur.fetchone()[0]:
                        cur.execute('select context from user where mobile_no=%s'%from_number)
                        context= json.loads(cur.fetchone()[0])
                else:
                        context={}   
                        
                
                print context
                language_translator = LanguageTranslator(
                        username='8994c77f-8245-4ca6-b7c9-adb32e44f6f4',
                        password='SPZZy6ybfzGb')

                language = language_translator.identify(txt_msg)                
                watsonDataDict = json.loads(json.dumps(language, indent=2))
                confidence1 = watsonDataDict["languages"][0]
                language_val1=confidence1["language"]
                confidence2 = watsonDataDict["languages"][1]
                language_val2=confidence2["language"]
                
                print language_val1
                print language_val2
                workspace_id='04c1f7c2-c655-46f8-9527-809809fc4282'
                if language_val1 == 'es' or language_val2== 'es':                        
                        workspace_id = 'b9757313-7979-48d7-88ac-e33241397980'
                
                
                

                response = conversation.message(
                        workspace_id=workspace_id,
                        message_input={'text': txt_msg},
                        context=context
                )
                
                dataDict = json.loads(json.dumps(response))        
                fetcontext = json.dumps(dataDict["context"])
                fetcontext1 = "'"+fetcontext+"'"
                print fetcontext1
                print "no"+from_number
                cur.execute('update user set context=%s where mobile_no=%s'%(fetcontext1,from_number))
                out_msg= dataDict["output"]["text"][0]
                action=dataDict["output"]["action"]
                print action
                print out_msg
                if action =='list':
                        account_list="\n"+"1-Checking 4954"+"\n"+"2-Savings 1256"+"\n"+"3-Creditcard 2572"
                        out_msg=out_msg%account_list
                elif action == 'list_spanish':
                        account_list="\n"+"uno-Checking 4954"+"\n"+"dos-Savings 1256"+"\n"+"Tres-Creditcard 2572"
                        out_msg=out_msg%account_list
                elif action == 'final':
                        acct_index= dataDict["context"]["acct_index"]
                        print acct_index
                        acct=''
                        bal=''
                        if acct_index == 1:
                                acct="Checking 4954"
                                bal="$1232"
                        if acct_index ==2:
                                acct="Saving 1256"
                                bal="$1000"
                        if acct_index == 3:
                                acct="Creditcard 2572"
                                bal="$10000"
                        out_msg=out_msg%(acct,bal)
                elif action == 'final_spanish':
                        acct_index= dataDict["context"]["acct_index"]
                        print acct_index
                        acct=''
                        bal=''
                        if acct_index == 'uno':
                                acct="Checking 4954"
                                bal="$1232"
                        if acct_index =='dos':
                                acct="Saving 1256"
                                bal="$1000"
                        if acct_index == 'Tres':
                                acct="Creditcard 2572"
                                bal="$10000"
                        out_msg=out_msg%(acct,bal)
                elif action == 'balance':
                        cur.execute('select ab.available_bal from user u,account_balance ab where ab.olb_id=u.olb_id and ab.acct_type="Checking" and u.mobile_no=%s'%from_number)
                        balance=cur.fetchone()[0]
                        out_msg = 'Checking account balance is $%s'%balance
                elif action == 'interest':
                        int_year=''
                        int_type=''
                        entities= dataDict["entities"]
                        if entities:                        
                                for ent in entities:
                                    if ent["entity"] == 'Interest_Year':
                                        int_year = ent["value"]
                                    if ent["entity"] == 'Mortgage_Type':
                                        int_type = ent["value"]
                        if int_year=='15 years' and int_type == 'fixed':
                                rate='3.25%'
                                out_msg=out_msg%rate
                        if int_year=='30 years' and int_type == 'refinance':
                                rate='4.25%'
                                out_msg=out_msg%rate
                elif action == 'transaction':
                        entities= dataDict["entities"]                
                        if entities:
                                number=''
                                for ent in entities:
                                    if ent["entity"] == 'sys-number':
                                        number = ent["value"]
                        print number
                        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
                        olb_id=cur.fetchone()[0]
                        print olb_id
                        if number:                        
                                cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s LIMIT %s'%(olb_id,number))
                                if cur.fetchall():                                                                                                                                                                        
                                        cur.execute('select td.date,td.tran_amount,td.tran_desc from transaction_details td,payee_details pd where td.payee_id=pd.payee_id and td.olb_id=%s order by td.date desc  LIMIT %s'%(olb_id,number))
                                        data=cur.fetchall()
                                        print data
                                        string_result = ''
                                        string_result +='Date   Amount  Description'+'\n'
                                        for row in data:                                                                                        
                                                sringout= str(row).replace("(", "").replace(")","").split(',')
                                                outstring = ''
                                                for index in range(len(sringout)):                                                                                                
                                                        if(index==1):
                                                                tempString = str(sringout[index]).replace("u","").replace("'","").replace(" ", "")
                                                                outstring += " $"+tempString
                                                        else:
                                                                outstring += str(sringout[index]).replace("u","").replace("'","")                                                                                             
                                                print outstring
                                                string_result += outstring + '\n'                                                                                                                                                                        
                                        print string_result
                                        out_msg = out_msg%string_result
                elif action == 'bill':
                        entities= dataDict["entities"]
                        period=''
                        print "23"
                        if entities:                        
                                for ent in entities:
                                    if ent["entity"] == 'period':
                                        period = ent["value"]
                        startDate=time.strftime("%m/%d/%Y")
                        Date=time.strftime("%m/%d/%Y")
                        if period == 'today':
                                Date=Date
                        elif period == 'tomorrow':
                                Date=datetime.datetime.strptime(Date, "%m/%d/%Y")
                                tempDate = Date + datetime.timedelta(days=1)
                                Date =  tempDate.strftime('%m/%d/%Y')
                                startDate = tempDate.strftime('%m/%d/%Y')
                        else:
                                print "else"
                                Date=datetime.datetime.strptime(Date, "%m/%d/%Y")
                                tempDate = Date + datetime.timedelta(days=7)
                                Date =  tempDate.strftime('%m/%d/%Y')                                                        
                        print Date
                        print startDate
                        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
                        olb_id=cur.fetchone()[0]                                                        
                        print '1'
                        cur.execute('select payment_date,nickname,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                        if cur.fetchall():                                
                                cur.execute('select payment_date,nickname,payment_desc,tran_amount from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                data=cur.fetchall()                                                                                
                                string_result = ''                                                                
                                for row in data:                                                                                        
                                                sringout= str(row).replace("(", "").replace(")","").split(',')
                                                outstring = ''
                                                for index in range(len(sringout)):                                                                                                
                                                                if(index==2):
                                                                                tempString = str(sringout[index]).replace("u","").replace("'","").replace(" ", "")
                                                                                outstring += " $"+tempString
                                                                else:
                                                                                outstring += str(sringout[index]).replace("u","").replace("'","")                                                                                             
                                                print outstring
                                                string_result += outstring + '\n'
                                cur.execute('select sum(tran_amount) from payment_details pd, payee_details p where p.payee_id=pd.payee_id and pd.olb_id=%s and pd.payment_date between %s and %s'%(olb_id,"'"+startDate+"'","'"+Date+"'"))
                                total = cur.fetchone()[0]
                                if total is None:
                                                total=0
                                string_result +='Total due Bill amount is $%s'%total
                                out_msg = string_result
                        else:
                                out_msg = 'No Bills Due.'
                elif action == 'spent':
                        entities= dataDict["entities"]
                        retailname=[]
                        print "23"
                        if entities:                        
                                for ent in entities:
                                    if ent["entity"] == 'retail_name':
                                        retailname.append(ent["value"])
                        cur.execute('select olb_id from user where mobile_no=%s'%from_number)
                        olb_id=cur.fetchone()[0]
                        
                        string_result = ''
                        string_result +='Please find the below details'+'\n\n'
                        
                        if not retailname:
                                out_msg = 'Please specify the shop or payment description'
                        else:
                                for desc in retailname: 
                                        querystring="'%"+desc.lower()+"%'"
                                        cur.execute('select sum(tran_amount) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                        balance=cur.fetchone()[0]
                                        if balance is None:
                                                balance = 0
                                        else:
                                                date_format = "%Y-%m-%d"
                                                cur.execute('select max(date) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                                max_date=cur.fetchone()[0]
                                                cur.execute('select min(date) from transaction_details where olb_id = %s and tran_desc like %s'%(olb_id,querystring))
                                                min_date=cur.fetchone()[0]
                                                a = datetime.datetime.strptime(min_date, date_format).date()
                                                b = datetime.datetime.strptime(max_date, date_format).date()
                                                delta = b - a                                                                                
                                        string_result += 'You spent $%s on %s between %s and %s.'%(balance,desc,a,b)+'\n'
                                out_msg = string_result
                elif action == 'dispute':
                        account_sid = "ACfaf705ecdfa9632e9d41c3cbdb94a451"
                        auth_token  = "ebddfe1b515e0c3c49e78454f3381d19"
                        client = TwilioRestClient(account_sid, auth_token)
                        cur.execute('select mobile_no from user where mobile_no=%s'%from_number)
                        mobile_num=cur.fetchone()[0]
                        if(mobile_num=='+19193997682'):
                                        mobile_num='+917358384976' 
                        call = client.calls.create(url="http://demo.twilio.com/docs/voice.xml",to=mobile_num,from_="+15084434500")
                        print(call.sid)
                        out_msg="For dispute related queries, support team of customer experience center will contact you shortly."
                        
        else:
                print 'else'
                out_msg='No user with this mobile number enrolled'
                 
                                                    
        print out_msg
        db.commit()
        cur.close()
        db.close()
        return out_msg

@app.route("/tapcoInAppBot", methods=['GET', 'POST'])
def tapcoInAppBot():
        """Send a dynamic reply to an incoming text message"""
        out_msg='How may i help you?'
        
        txt_msg=request.values.get('Body', None).encode('utf-8')
        from_number=request.values.get('From', None)
        print txt_msg
        if txt_msg.lower() == 'hola':
                out_msg='Gracias por ponerse en contacto con NewGen. ¿Con qué puedo ayudarte? Algunas cosas que usted puede preguntarme: La cotización del dueño de una casa nueva, encuadernar una cotización, informar una nueva reclamación, el estado en mi demanda etc.'
        else:                
                ai = apiai.ApiAI('9ad560fb862e41f8a1b8c55ca5ea2ff0')
                requ = ai.text_request()
                requ.lang = 'en'  # optional, default value equal 'en'
                requ.session_id = from_number
                requ.query = txt_msg                
                respo = requ.getresponse()
                #print (response.read())
                out_resp= json.loads(respo.read())
                out_msg= out_resp["result"]["fulfillment"]["speech"]
        
        return out_msg
		
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    #print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
        db = mysql.connector.connect(host="59831ab27628e1f85900000d-trialchatbot.rhcloud.com", port=57521, user="adminjuz6bQy", passwd="jSw9dbFyIxtx", db="chatbot")
        cur = db.cursor()
        if req.get("result").get("action") == "quote":            
                result = req.get("result")
                parameters = result.get("parameters")
                name = parameters.get("name")
                state = parameters.get("state")
                zipcode = parameters.get("zipcode")
                policyterm = parameters.get("policy-term")
                builtyear = parameters.get("built-year")
                type1 = 'Residential'
                area = parameters.get("area")
                term = parameters.get("term")
                quote_id=id_generator()                
                print quote_id+name+state+zipcode+policyterm+builtyear+type1+area
                if term.lower() == 'y' or term.lower() == 'yes':
                        if int(builtyear) <= 2017:
                                cur.execute('insert into quote_details values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'%("'"+quote_id+"'","'"+name+"'","'"+state+"'","'"+zipcode+"'","'"+policyterm+"'","'"+builtyear+"'","'"+type1+"'","'"+area+"'","'"+time.strftime('%Y-%m-%d')+"'"))
                                speech = 'Your quote id is '+quote_id+'\n'+'Do you want any other quote request, Please specify the insurance type?'
                        else:
                                speech = 'Year should not be in future.'
                                
                        
                else:
                        speech='Not accepted'

                print("Response:")
                print(speech)
        elif req.get("result").get("action") == "newclaim.newclaim-no.newclaim-no-custom.newclaim-no-custom-custom" or req.get("result").get("action") == "newclaim.newclaim-yes.newclaim-yes-custom":
                result = req.get("result")
                parameters = result.get("parameters")               
                losstype = parameters.get("losstype")
                lossdate = parameters.get("lossdate")                
                lossamount = parameters.get("lossamount")
                print losstype
                status='Processing'
                claim_type='property'
                loss_descr='description'
                claim_id=id_generator()                
                cur.execute('insert into claim_details values(%s,%s,%s,%s,%s,%s,%s)'%("'"+claim_id+"'","'"+claim_type+"'","'"+losstype+"'","'"+lossdate+"'","'"+loss_descr+"'","'"+lossamount+"'","'"+status+"'"))
                speech = 'I have created a claim report. Please make a note of the claim id '+claim_id+' for your reference. A qualified claim adjuster will soon get in touch with the claimant to process the claim further.'
        elif req.get("result").get("action") == "existing_claim":
                result = req.get("result")
                parameters = result.get("parameters")
                claimid = parameters.get("claimid")
                print claimid
                cur.execute('SELECT loss_amount from claim_details where claim_id=%s'%("'"+claimid.upper()+"'"))
                #print cur.fetchone()
                status_data = cur.fetchone()
                print status_data
                if status_data is None:
                        speech = 'I am sorry I could not provide you information regarding your claim. Do you want me to arrange a call back from claims services department to further assist you?'
                else:
                        speech = 'Thanks for the details. I found the claim you are looking for. Claim id '+claimid+' with an estimated loss amount $'+status_data[0]+' is being worked by claim adjuster Mr. John Smith. Please give 2 to 4 business days to complete the claim processing.'+'\n'+'Is there anything else I can help you with do?'
        elif req.get("result").get("action") == "existing_claim_spanish":
                result = req.get("result")
                parameters = result.get("parameters")
                claimid = parameters.get("claimid.original")
                print claimid
                cur.execute('SELECT loss_amount from claim_details where claim_id=%s'%("'"+claimid.upper()+"'"))
                #print cur.fetchone()
                status_data = cur.fetchone()
                print status_data
                if status_data is None:
                        speech = 'Siento no poder proporcionarle información sobre su reclamo. ¿Quieres que llame de nuevo al departamento de servicios de reclamos para que te ayude?'
                else:
                        print claimid+status_data[0]
                        speech = 'Gracias por los detalles. He encontrado la reclamación que está buscando. Reclamación de '+claimid.encode("utf-8")+' con una cantidad de pérdida estimada $'+status_data [0].encode("utf-8")+' está siendo trabajado por el ajustador de reclamaciones Sr. John Smith. Por favor dé 2 a 4 días hábiles para completar el proceso de reclamación.'
                        
        elif req.get("result").get("action") == "Binding":
                result = req.get("result")
                parameters = result.get("parameters")
                quoteid = parameters.get("quoteid")
                print quoteid
                cur.execute('SELECT date_created,insured_name,state,zip,term,year,area from quote_details where quote_id=%s'%("'"+quoteid.upper()+"'"))
                status_data = cur.fetchone()
                print status_data                
                if status_data is None:
                        speech = 'Unfortunately I could not locate the quote id mentioned.'
                else:                                        
                        speech = 'I found the quote you mentioned in your query. This quote was generated on '+status_data[0]+', Insured name - '+status_data[1]+', General Liability - $3000,000, Advertising Injury Limit - $2500, Medical Limit - $1000. One time premium (offers 10% discount) - $810, monthly premium $150. Policy Term '+status_data[4]+' months. Please confirm Y or N'                        
        elif req.get("result").get("action") == "Binding.Binding-custom":
                result = req.get("result")
                parameters = result.get("parameters")
                flag = parameters.get("flag")
                if flag.lower() == 'y' or flag.lower() == 'yes':
                        speech = 'Thank you for providing me with the details. I have placed a policy binding request on your behalf. You will receive a call back from underwriting services departemt to confirm the binding. Is there anything else I can help you with?'
                else:
                        speech='No problem. Thank you for contacting MGA Underwriters! We appreciate your business.'
        elif req.get("result").get("action") == "Newquote.Newquote-custom.Newquote-custom-custom":
                result = req.get("result")
                sender_id = req.get("sessionId")
                parameters = result.get("parameters")
                flag = parameters.get("flag")
                print sender_id
                print flag
                if flag.lower() == 'y' or flag.lower() == 'yes':
                        speech = 'MGA agent will contact you shortly.'
                        account_sid = "ACfaf705ecdfa9632e9d41c3cbdb94a451"
                        auth_token  = "ebddfe1b515e0c3c49e78454f3381d19"
                        client = TwilioRestClient(account_sid, auth_token)
                        cur.execute('select u.mobile_no from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                        if cur.fetchone():
                                cur.execute('select u.mobile_no from user u,fb_chatbot fb where u.auth_code=fb.auth_code and fb.sender_id=%s'%sender_id)
                                mobile_num=cur.fetchone()[0]
                        else:
                                cur.execute('select mobile_no from user where auth_code=%s'%sender_id)
                                mobile_num=cur.fetchone()[0]
                                print 'mobile2'                        
                        print mobile_num                                               
                        if(mobile_num=='+19193997682'):
                                mobile_num='+917358384976' 
                        call = client.calls.create(url="http://demo.twilio.com/docs/voice.xml",to=mobile_num,from_="+15084434500")
                else:
                        speech='okay, thank you have a good day.'
        elif req.get("result").get("action") == "Existingclaim.Existingclaim-custom":
                result = req.get("result")
                parameters = result.get("parameters")
                flag = parameters.get("flag")
                if flag.lower() == 'y' or flag.lower() == 'yes':
                        speech = 'Sure. I have arranged a call back for you. Is there anything else I can help you with?'
                else:
                        speech='Thanks you for contacting MGA. Have a great day!'
        elif req.get("result").get("action") == "new_claim":
                result = req.get("result")
                parameters = result.get("parameters")
                flag = parameters.get("policyholder")
                if flag.lower() == 'y' or flag.lower() == 'yes':
                        speech = 'Thanks for the details. Please provide me with claim details such as, reason of loss, loss type and estimated loss amount.'
                else:
                        speech='Please provide me the Claimant name, address and phone number.'
        elif req.get("result").get("action") == "clear":
                ai = apiai.ApiAI('9ad560fb862e41f8a1b8c55ca5ea2ff0')
                requ = ai.text_request()
                requ.lang = 'en'  # optional, default value equal 'en'
                requ.session_id = from_number
                requ.query = txt_msg                
                respo = requ.getresponse()
                
        
                
                
        else:
                return {}

        db.commit()
        cur.close()
        db.close()
        

        return {
                "speech": speech,
                "displayText": speech,
        # "data": data,
        # "contextOut": [],
                "source": "apiai-tapco-sample"
        }
  		

def id_generator(size=5, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))


@app.route('/ChatBot2', methods=["POST"])
def ChatBot2():        
        return "hello"



if __name__ == '__main__':
        app.run()
