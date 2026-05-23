#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: llm.py
#   REVISION: October, 2024
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   The parts of the web application that handle interacting with the LLM
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os, datetime, time, random, hashlib, json, copy
#
from rebert._prototype_8_.web.config import *
from rebert._prototype_8_.web.prompts import *
from rebert._prototype_8_.web.utilities import *
#
#
#   This comes from the rebert class library and manages API keys
#   You should use it to store your OpenAI API key locally, so your
#   key is not stored as a constant in the code.
from rebert.classes.data.KeyManager import KeyManager
#
#   This class encapsulates the OpenAI chat completion API. It is
#   a 'souped up' version of the calls that were being made to
#   the requests library in the prior prototypes. This Chat class
#   will help with some error handling and simplify how we make
#   API calls.
from rebert.classes.OpenAI.Chat import Chat
#
#   These two classes are data structures that help construct and
#   manage the chat request body. As our requests get more complex
#   we will want a way to manage them.
from rebert.classes.OpenAI.payload.ChatMessage import ChatMessage
from rebert.classes.OpenAI.payload.ChatRequestPayload import ChatRequestPayload
#
#
#

MODULE_LLM_DEBUG = True

if not MODULE_DEBUG_OVERRIDE:
    MODULE_LLM_DEBUG = GLOBAL_DEBUG


##############
#
#   OpenAI - LLM
#
##############
#
#   The code needs to maintain the status of the chat. This status 
#   will include parameters that tell the model how it should respond
#   as well as all of the user questions and the responses.
#
def new_root_context(movie_data_str=""):
    chat_context = ChatRequestPayload()
    sprompt = ROOT_CONTEXT_PROMPT.format(movie_data_str=movie_data_str)
    
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)
    
    chat_context.addMessage(system_turn)
    return chat_context
#
#
def new_discussion_context(movie_title="", reviews_str=""):
    chat_context = ChatRequestPayload()
    sprompt = MOVIE_CONTEXT_PROMPT.format(movie_title=movie_title,
                                          movie_review_str=reviews_str)
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)
    
    chat_context.addMessage(system_turn)
    return chat_context
#
#
def new_root_context(movie_data_str=""):
    chat_context = ChatRequestPayload()
    sprompt = ROOT_CONTEXT_PROMPT.format(movie_data_str=movie_data_str)
    
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)
    
    chat_context.addMessage(system_turn)
    return chat_context

#
#
#   This sets the configuration parameters, based on constants defined in the
#   config.py file. If a constant is undefined, then this will use the model
#   default value.
def configure_model_params(chat_context=None):
    #   If there is no chat context, raise an error
    if not chat_context:
        raise Exception("No chat_context has been supplied")
    #
    #   Set configuration values
    used_pres_penalty = False
    try:
        chat_context.setModel(REBERT_LLM_MODEL)
    except NameError as ex:
        print_server_log(f"There must be a model to make a request!","make_chat_request()",
                        MODULE_LLM_DEBUG)
        print_server_log(f"Caught exception","make_chat_request()",MODULE_LLM_DEBUG)
        print_server_log(f"{e}","make_chat_request()",MODULE_LLM_DEBUG)
        raise
    
    try:
        chat_context.setTemperature(REBERT_LLM_TEMPERATURE)
    except NameError as e:
        pass
        #print_server_log(f"Using default LLM temperature","configure_model_params()",
        #                MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)
    
    try:
        chat_context.setMaxTokens(REBERT_LLM_TOKEN_LIMIT)
    except NameError as e:
        pass
        #print_server_log(f"Using default max completion tokens", "configure_model_params()",
        #                MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)
    
    try:
        chat_context.setPresencePenalty(REBERT_LLM_PRES_PENALTY)
        used_pres_penalty = True
    except NameError as e:
        pass
        #print_server_log(f"Using default LLM presence_penalty","configure_model_params()",
        #                MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)

    #
    #   Can only use one of either frequency penalty or presence penalty
    if not used_pres_penalty:
        try:
            chat_context.setFrequencyPenalty(REBERT_LLM_FREQ_PENALTY)
        except NameError as e:
            pass
            #print_server_log(f"Using default LLM frequency_penalty","configure_model_params()",
            #                MODULE_LLM_DEBUG)
            #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
            #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)
    
    return chat_context
#
#
#   Making a request is about modifying the growing chat_context
#   setting up the HTTP request URL and request headers, and making
#   the request.
def make_chat_request(chat_context=None, chat_key=""):
    #   If there is no chat context, raise an error
    if not chat_context:
        print_server_log(f"No chat_context was supplied","make_chat_request()",
                        MODULE_LLM_DEBUG)
        raise Exception("No chat_context has been supplied")
    
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    #
    #   Set configuration values
    chat_context = configure_model_params(chat_context)
    #    
    chat_api.setRequestPayload(chat_context.json(clean=True))
    chat_api.queueRequest()
    chat_api.makeRequest()
    response = chat_api.nextResponse()
    resp_dict = response.json()
    
    #   There is a lot in the response - just extract the message
    assistant_turn = ChatMessage()
    message = resp_dict['choices'][0]['message']
    assistant_turn.setRole("assistant")
    assistant_turn.setMessage(message)
    
    return assistant_turn
#
#   Generate a string of KEY:value items for each movie
#   Keys should correspond to the keys defined in the
#   ROOT_CONTEXT_PROMPT
#
#   This prototype adds the SYNOPSIS key and inserts that
#   value when creating the prompt data string.
def create_movie_info_str(movie_list=[]):
    movie_info_str = ""
    for movie in movie_list:
        data = f"\tMOVIE TITLE: {movie['title']}\n"
        note = movie['notes'].partition(',')[0]
        data = data + f"\tRELEASE TYPE: {note}\n"
        data = data + f"\tOPENING DATE: {movie['opening_date_str']}\n"
        data = data + f"\tSYNOPSIS: {movie['synopsis']}\n"
        if not movie_info_str:
            movie_info_str = data
        else:
            movie_info_str = movie_info_str + "\n" + data
    return movie_info_str

def create_movie_review_str(review_list=[]):
    movie_review_str = str()
    for review in review_list:
        data = f"REVIEW OF: {review['title']}\n"
        data = data + f"REVIEW AUTHOR: {review['author']}\n"
        data = data + f"REVIEW TEXT: {review['review']}\n"
        data = data + f"REVIEW SUMMARY SCORE: {review['rating_str']}\n"
        data = data + f"REVIEW SOURCE: {review['source']}\n"
        if not movie_review_str:
            movie_review_str = data
        else:
            movie_review_str = movie_review_str + "\n" + data
    return movie_review_str
#
#
#
def new_user_turn(user_text=""):
    user_turn = ChatMessage()
    user_turn.setRole("user")
    user_turn.setContent(user_text)
    return user_turn
#
#
#
def restore_chat_context(session_state=None):
    chat_context = ChatRequestPayload()
    chat_turns = session_state['chat_turns'][session_state['active_branch']]
    for turn in chat_turns:
        chat_message = ChatMessage()
        chat_message.setMessage(turn)
        chat_context.addMessage(chat_message)
    return chat_context
#
#
#
def create_ephem_qna_str(session=None):
    #
    #   Construct the question and answer string, based on what we have from the user
    qna_str = str()
    for i in range(1,4):
        if session['ephem_status'][str(i)]['response']:
            print_server_log(f"Have Q&A pair {i}",
                            "create_ephem_qna_str()",
                            MODULE_LLM_DEBUG)
            qna_str = qna_str + f"QUESTION:\n\t{session['ephem_status'][str(i)]['prompt']}\n"
            qna_str = qna_str + f"ANSWER:\n\t{session['ephem_status'][str(i)]['response']}\n"
    qna_str = qna_str+"\n"
    return qna_str
#
#
#   If session data is provided, then it produces a prompt that includes
#   both movie information and the data from the prior questions.
#
#   If only qna_str is provided, then it only uses the qna_str to make a
#   request for a new question
#
def qna_question_request(session=None, qna_str="", chat_key=""):
    #   Must have a qna_str to make the request
    if not qna_str:
        print_server_log(f"Missing Q&A string!",
                        "qna_question_request()",
                        MODULE_LLM_DEBUG)
        raise Exception(f"Missing Q&A string!")
    
    #
    #   Construct a movie info string that might help the LLM think about a good question
    if session:
        info_str = str()
        highlights = session['highlights']
        for movie in highlights:
            info_str = info_str + f"TITLE:\n\t{movie['title']}\n"
            info_str = info_str + f"SYNOPSIS:\n\t{movie['synop']}\n"
        info_str = info_str+"\n"
        sprompt = EPHEM_QUESTION_SYSTEM_PROMPT2.format(movie_info=info_str,
                                                       ephem_qna_pairs=qna_str)
    else:
        sprompt = EPHEM_QUESTION_SYSTEM_PROMPT1.format(ephem_qna_pairs=qna_str)

    chat_context = ChatRequestPayload()
    
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)    
    chat_context.addMessage(system_turn)

    user_turn = ChatMessage()
    user_turn.setRole("user")
    user_turn.setContent(EPHEM_QUESTION_PROMPT)
    chat_context.addMessage(user_turn)
    
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    #
    #   Set configuration values
    chat_context = configure_model_params(chat_context)
    #    
    chat_api.setRequestPayload(chat_context.json(clean=True))
    chat_api.queueRequest()
    chat_api.makeRequest()
    response = chat_api.nextResponse()
    resp_dict = response.json()
    
    #   There is a lot in the response - just extract the message
    assistant_turn = ChatMessage()
    message = resp_dict['choices'][0]['message']
    assistant_turn.setRole("assistant")
    assistant_turn.setMessage(message)
    
    return assistant_turn



def make_ephem_rec_request(session=None, chat_key=""):
    #
    #   Construct a description string from what we know about user's likes
    user_description = str()
    for i in range(1,4):
        if session['ephem_status'][str(i)]['response']:
            user_description = user_description +" "+ session['ephem_status'][str(i)]['response']
    user_description = user_description+"\n\n"
    #
    #   Need to create an record for each request - this will be parallelized
    threaded_requests = list()
    for movie in session['highlights']:
        #   Create a dictionary for the threaded request for the movie
        ephem_thread = REBERT_THREADED_EPHEM_REC_TEMPLATE.copy()
        ephem_thread['movie'] = movie
        ephem_thread['title'] = movie['title']
        ephem_thread['message'] = "still working"
        title_lower = movie['title'].lower()
        reviews = list()
        if title_lower in session['movie_data']['reviews']:
            reviews = session['movie_data']['reviews'][title_lower]
        review_str = create_movie_review_str(reviews)
        if user_description and review_str:
            #   Now, create the chat that we need to make the request
            ephem_thread['chat'] = ChatRequestPayload()
            system_turn = ChatMessage()
            system_turn.setRole("system")
            sprompt = EPHEM_RECOMMENDATION_PROMPT.format(movie_review_str=review_str,
                                                         user_description=user_description)
            system_turn.setContent(sprompt)
            ephem_thread['chat'].addMessage(system_turn)

            user_turn = ChatMessage()
            user_turn.setRole("user")
            uprompt = EPHEM_RECOMMENDATION_QUESTION.format(movie_title=movie['title'])
            user_turn.setContent(uprompt)
            ephem_thread['chat'].addMessage(user_turn)
            print_server_log(f"Creating API requester for '{ephem_thread['title']}'",
                            "make_ephem_rec_request()",
                            MODULE_LLM_DEBUG)
            ephem_thread['requester'] = Chat()
            ephem_thread['requester'].setBearerToken(chat_key)
            #   Set configuration values
            ephem_thread['chat'] = configure_model_params(ephem_thread['chat'])
            ephem_thread['requester'].setRequestPayload(ephem_thread['chat'].json(clean=True))
            #   Start thread
            ephem_thread['requester'].startThread()
            ephem_thread['requester'].queueRequest()
            ephem_thread['requester'].startRequest()
            print_server_log(f"Started requesting for '{ephem_thread['title']}'",
                            "make_ephem_rec_request()",
                            MODULE_LLM_DEBUG)
            threaded_requests.append(ephem_thread)
        # just going to do one movie for now ...
        #break
    #
    #   Now start checking on the running threads - before we start checking we'll
    #   wait a "big" amount to allow the requests time to complete. There is no need
    #   to check right away
    time.sleep(2.5)
    passes = 0
    waiting_completion = True
    #
    #   The waiting completion flag is set to True if any thread is still in
    #   the process of making a request or if the thread has response data that
    #   we have not yet collected from the thread
    while waiting_completion:
        waiting_completion = False
        passes += 1
        #   Sleep a small amount about 0.5 second between checks
        time.sleep(0.5)
        
        for ephem_thread in threaded_requests:
            if not ephem_thread['requester']: continue
            
            if ephem_thread['requester'].isRequesting():
                waiting_completion = True
                ephem_thread['count']+=1
                print_server_log(f"Pass [{passes:2}]: Check {ephem_thread['count']} on '{ephem_thread['title']}' - still requesting",
                                "make_ephem_rec_request()",
                                MODULE_LLM_DEBUG)
                continue
            #
            #   Collect the response - there should only be one response
            if ephem_thread['requester'].responses() > 0:
                waiting_completion = True
                ephem_thread['response'] = ephem_thread['requester'].nextResponse()
                ephem_thread['response'] = ephem_thread['response'].json()
                ephem_thread['message'] = ephem_thread['response']['choices'][0]['message']
                print_server_log(f"Pass [{passes:2}]: COLLECTING response for '{ephem_thread['title']}'",
                                "make_ephem_rec_request()",
                                MODULE_LLM_DEBUG)
            #
            #   Terminate, clean up, and dispose the thread
            if ephem_thread['requester'].isRunning() and ephem_thread['requester'].responses() == 0:
                ephem_thread['requester'].terminateThread()
                ephem_thread['requester'] = None
                print_server_log(f"Pass [{passes:2}]: TERMINATING thread for '{ephem_thread['title']}'",
                                "make_ephem_rec_request()",
                                MODULE_LLM_DEBUG)
        #
        #   At 0.5 seconds sleeping per cycle, this is equivalent to waiting ~50 seconds for
        #   a response from the LLM - that seems like a long time. Even some of the slowest
        #   responses observed are about 40-50 seconds for a complex request. This request
        #   isn't all that complex.
        if passes > 100: 
            print_server_log(f"Exceeded maximum allowed passes: {passes} > 100 - terminating waiting",
                            "make_ephem_rec_request()",
                             MODULE_LLM_DEBUG)
            waiting_completion = False
    
    #
    #   Run through each of the responses, parse out the response and rationale
    for ephem_thread in threaded_requests:
        #print_server_log(f"For '{ephem_thread['title']}'",
        #                "make_ephem_rec_request()",
        #                MODULE_LLM_DEBUG)
        #
        #   First, kill off any threads that might have been running
        if ephem_thread['requester']:
            ephem_thread['requester'].terminateThread()
            ephem_thread['requester'] = None
            #   Special case, was still requesting - no data to parse
            ephem_thread['movie']['rebert_response'] = "Rebert was not able to complete a match in the allowed time."
            ephem_thread['movie']['rebert_rating'] = "still working"
            ephem_thread['movie']['rebert_rationale'] = "Rebert was not able to complete a match in the allowed time."
        else:
            #   Now, parse out the response
            try:
                content = ephem_thread['message']['content']
                rating = content.partition("<MATCH>")[2]
                rating = rating.partition("</MATCH>")[0].strip()
                rationale = content.partition("<RATIONALE>")[2]
                rationale = rationale.partition("</RATIONALE>")[0].strip()
                ephem_thread['movie']['rebert_response'] = content
                ephem_thread['movie']['rebert_rating'] = rating
                ephem_thread['movie']['rebert_rationale'] = rationale
            except:
                print_server_log(f"Exception retrieving thread information for '{ephem_thread['title']}'",
                                "make_ephem_rec_request()")
                ephem_thread['movie']['rebert_response'] = "Rebert was not able to determine a recommendation. You might improve the recommendation by providing more information about movies you like."
                ephem_thread['movie']['rebert_rating'] = "still working"
                ephem_thread['movie']['rebert_rationale'] = "Rebert was not able to determine a recommendation. You might improve the recommendation by providing more information about movies you like."
        #print_server_log(f"For '{ephem_thread['movie']['title']}' RECOMMENDATION: '{ephem_thread['movie']['rebert_rating'] }'",
        #                  "make_ephem_rec_request()",
        #                  MODULE_LLM_DEBUG)
        #print_server_log(f"For '{ephem_thread['movie']['title']}' RATIONALE: '{ephem_thread['movie']['rebert_rationale'] }'",
        #                  "make_ephem_rec_request()",
        #                  MODULE_LLM_DEBUG)
    return session

#
#   Create a question & answer string to be used in prompt construction
#
def create_rating_qna_str(session=None):
    #
    #   Construct the question and answer string, based on what we have from the user
    qna_str = str()
    for item in session['rating']['in_progress']['qna']:
        qna_str = qna_str + f"QUESTION:\n\t{item['question']}\n"
        qna_str = qna_str + f"ANSWER:\n\t{item['answer']}\n"
    qna_str = qna_str+"\n"
    return qna_str

#
#   The idea here is to use the LLM to extract the potential titles
#   from the user text
#
def movie_title_extract_request(transcript=None, chat_key=""):
    #
    #   Prepare the chat context   
    chat_context = ChatRequestPayload()
    #   Setup the system prompt
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(RATE_EXTRACT_PROMPT)
    chat_context.addMessage(system_turn)
    #   Setup the user question, using transcript
    user_turn = ChatMessage()
    user_turn.setRole("user")
    userq = RATE_EXTRACT_QUESTION.format(transcript=transcript['text'])
    user_turn.setContent(userq)
    chat_context.addMessage(user_turn)
    
    #   Grab the starting time
    start_time = datetime.datetime.now()
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    #
    #   Set configuration values
    chat_context = configure_model_params(chat_context)
    #    
    chat_api.setRequestPayload(chat_context.json(clean=True))
    chat_api.queueRequest()
    chat_api.makeRequest()
    response = chat_api.nextResponse()
    resp_dict = response.json()
    #   Grab the finishing time
    finish_time = datetime.datetime.now()
    runtime = finish_time - start_time
    print_server_log(f"Title extraction elapsed time: {runtime}",
                      "movie_title_extract_request()",
                      MODULE_LLM_DEBUG)
    #   Get the text of the response
    message = resp_dict['choices'][0]['message']['content']
    #   If there were no titles identified, we're done
    if "MISSING_MOVIE_TITLES" in message: 
        print_server_log(f"No movie titles identified in transcript.",
                          "movie_title_extract_request()",
                          MODULE_LLM_DEBUG)    
        return transcript
    titles = list()
    title_parts = message.partition("<TITLE>")
    title_parts = title_parts[2].partition("</TITLE>")
    while title_parts[1]:
        if title_parts[0]:
            titles.append(title_parts[0])
        title_parts = title_parts[2].partition("<TITLE>")
        title_parts = title_parts[2].partition("</TITLE>")
    print_server_log(f"Extracted titles: {str(titles)}",
                      "movie_title_extract_request()",
                      MODULE_LLM_DEBUG)    
    transcript['titles'] = titles
    return transcript

#######
#
#   BANTER RECOMMENDATIONS
#
#

#
#   Create/Setup the banter critic
#
def new_banter_critic_setup(critic=None, title="", session_state=None):
    #
    title_lower = title.lower()
    #
    #   Collect the synopsis for the movie
    synopsis = ""
    for movie in session_state['movie_data']['openings']:
        if movie['title'] == title:
            synopsis = movie['synopsis']
            break
    #
    #   Now, create a movie review string
    review_list = []
    if title_lower in session_state['movie_data']['reviews']:
        review_list = session_state['movie_data']['reviews'][title_lower]
    #
    #   We set up to possibly sample from the full set of reviews
    #   This provides a chance that the critics have a different views
    #   to express because they have different information from different
    #   reviewers
    review_count = len(review_list)     # the total number of reviews we have
    
    print_server_log(f"Have {review_count} reviews for '{title}'",
                     "new_banter_critic_setup()",
                     MODULE_LLM_DEBUG)
    #   Do the sampling if there are 4 or more reviews
    if review_count > 3:
        sample_size = review_count//2 + 1
        if review_count > 8: sample_size += 1
        review_list = random.sample(review_list, sample_size)
    
    print_server_log(f"Critic {critic['key']}:{critic['name']} using {len(review_list)}/{review_count} reviews for '{title}'",
                     "new_banter_critic_setup()",
                     MODULE_LLM_DEBUG)
    
    movie_review_str = create_movie_review_str(review_list)
    #
    #   Then we can create the system prompt for this critic
    sprompt = critic['prompt'].format(movie_title = title,
                                      movie_synopsis = synopsis,
                                      movie_review_str = movie_review_str)
    sprompt = sprompt.strip()
    
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)
    system_turn.setName(f"CriticBanter_Setup_{critic['key']}_{critic['name']}")
    return system_turn

#
#   Make a chat request for a banter critic
#
def critic_banter_chat_request(chat_turns=None, critic=None, opp_critic_comment="", title="", chat_key=""):
    #
    #   Need to rebuild the chat context from the messages
    chat_context = ChatRequestPayload()
    chat_context = configure_model_params(chat_context)
    try:
        chat_context.setMaxTokens(REBERT_BANTER_MAX_TOKENS)
        print_server_log(f"Set max completion tokens to {REBERT_BANTER_MAX_TOKENS}",
                        "critic_banter_chat_request()",
                        MODULE_LLM_DEBUG)
    except NameError as e:
        print_server_log(f"Using default max completion tokens",
                        "critic_banter_chat_request()",
                        MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","critic_banter_chat_request()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","critic_banter_chat_request()",MODULE_LLM_DEBUG)
    #
    #   Add all of the messages/turns
    for turn in chat_turns:
        chat_message = ChatMessage()
        chat_message.setMessage(turn)
        chat_context.addMessage(chat_message)
    #
    #   Build out a prompt based on the opposing critics comment
    if opp_critic_comment:
        comment = f"The other critic just made this comment about the film:\n\"{opp_critic_comment}\"\n"
    else:
        comment = "The other critic is listening to your comment."
    req_prompt = BANTER_PROMPT_CRITIC.format(movie_title = title,
                                             critic_comment = comment)
    #
    #   Create a turn to reflect that new prompt and add it to the context
    name_info = f"{critic['key']}_{critic['name']}"
    user_turn = ChatMessage()
    user_turn.setRole("user")
    user_turn.setContent(req_prompt)
    user_turn.setName(f"CriticBanter_Request_{name_info}")
    chat_context.addMessage(user_turn)
    #
    #   Create a chat API object, add the chat context as a payload, 
    #   make the request, and get the response
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    chat_api.setRequestPayload(chat_context.json(clean=True))
    #print_server_log(f"Payload:\n{chat_context.json(clean=True,indent=4)}",
    #                "critic_banter_chat_request()",
    #                MODULE_LLM_DEBUG)
    chat_api.queueRequest()
    chat_api.makeRequest()
    response = chat_api.nextResponse()
    resp_dict = None
    if not response:
        prior = chat_api.getPriorRequests()[0]
        print_server_log(f"ERROR:\n{json.dumps(prior['error'],indent=4)}",
                        "critic_banter_chat_request()",
                        MODULE_LLM_DEBUG)
        return [None, None]
    else:
        resp_dict = response.json()
    #
    #   Add the response to the chat context, as an assistant turn
    assistant_turn = ChatMessage()
    message = resp_dict['choices'][0]['message']
    assistant_turn.setRole("assistant")
    assistant_turn.setMessage(message)
    assistant_turn.setName(f"CriticBanter_Response_{name_info}")

    return [user_turn, assistant_turn]

#
#   Make a chat request for the user. This is where the user asks
#   a question or makes a comment - the critics both need a chance to
#   respond to the user.
#
#   One or more of the responses needs to be held back to wait for
#   the appropriate critic timing to respond.
#
def user_banter_chat_request(critics=None, banter_context=None, user_comment="", title="", chat_key=""):
    #
    #   Need to rebuild the chat context for both critics
    #   c1 = critic 1
    #   c2 = critic 2
    c1_context = ChatRequestPayload()
    c1_context = configure_model_params(c1_context)
    c2_context = ChatRequestPayload()
    c2_context = configure_model_params(c2_context)
    try:
        c1_context.setMaxTokens(REBERT_BANTER_MAX_TOKENS)
        c2_context.setMaxTokens(REBERT_BANTER_MAX_TOKENS)
        print_server_log(f"Set max completion tokens to {REBERT_BANTER_MAX_TOKENS}",
                        "user_banter_chat_request()",
                        MODULE_LLM_DEBUG)
    except NameError as e:
        print_server_log(f"Using default max completion tokens",
                        "user_banter_chat_request()",
                        MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","critic_banter_chat_request()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","critic_banter_chat_request()",MODULE_LLM_DEBUG)
    #
    #
    #   We need to construct two turns, one for each critic to "hear" what
    #   the user said
    c1 = critics["critic_1"]
    c1_name = f"{c1['key']}_{c1['name']}"
    for turn in banter_context["critic_1_chat"]:
        chat_message = ChatMessage()
        chat_message.setMessage(turn)
        c1_context.addMessage(chat_message)

    c2 = critics["critic_2"]
    c2_name = f"{c2['key']}_{c2['name']}"
    for turn in banter_context["critic_2_chat"]:
        chat_message = ChatMessage()
        chat_message.setMessage(turn)
        c2_context.addMessage(chat_message)
    
    #
    #   Build out a prompt based on user's comment
    if user_comment:
        comment = f"The third party made this comment about the film:\n\"{user_comment}\"\n\nYou might specifically address their question or comment in your response."
    else:
        comment = "The third party is listening to your comment."
    req_prompt = BANTER_PROMPT_USER.format(movie_title = title,
                                           user_comment = comment)
    #
    #   Create a turns with the new prompt and add it to the context
    #   one for each critic
    u1 = ChatMessage()
    u1.setRole("user")
    u1.setContent(req_prompt)
    u1.setName(f"UserBanter_Request_{c1_name}")
    c1_context.addMessage(u1)
    #
    u2 = ChatMessage()
    u2.setRole("user")
    u2.setContent(req_prompt)
    u2.setName(f"UserBanter_Request_{c2_name}")
    c2_context.addMessage(u2)
    #
    #   Get ready to launch two requests, one for each critic - threaded
    c1_api = Chat()
    c1_api.setBearerToken(chat_key)
    c1_api.setRequestPayload(c1_context)
    c1_api.startThread()
    c1_api.queueRequest()
    c2_api = Chat()
    c2_api.setBearerToken(chat_key)
    c2_api.setRequestPayload(c2_context)
    c2_api.startThread()
    c2_api.queueRequest()
    #
    #   Now, start the requests
    c1_api.startRequest()
    print_server_log(f"Started request for '{c1_name}'",
                    "user_banter_chat_request()",
                    MODULE_LLM_DEBUG)
    c2_api.startRequest()
    print_server_log(f"Started request for '{c2_name}'",
                    "user_banter_chat_request()",
                    MODULE_LLM_DEBUG)
    #
    #   Now start checking on the running threads - before we start checking we'll
    #   wait a "big" amount to allow the requests time to complete. There is no need
    #   to check right away
    time.sleep(1.75)
    passes = 0
    waiting_completion = True
    #
    #   The waiting completion flag is set to True if either thread is still requesting
    while waiting_completion:
        waiting_completion = False
        passes += 1
        time.sleep(0.33)
        #
        if c1_api.isRequesting() or c2_api.isRequesting():
            waiting_completion = True
            print_server_log(f"Pass [{passes:2}]: still requesting",
                              "user_banter_chat_request()",
                              MODULE_LLM_DEBUG)
        #   
        #   At some point we just have to give up - this will be about 25 seconds
        if passes > 125: waiting_completion = False
    
    #
    #   Get response for critic 1
    #
    c1_resp = c1_api.nextResponse()
    if c1_resp:
        resp_dict = c1_resp.json()
        a1 = ChatMessage()
        message = resp_dict['choices'][0]['message']
        a1.setMessage(message)
        a1.setName(f"UserBanter_Response_{c1_name}")
        #   Save the critic response and mark that there is a critic comment ready
        #   Save the user message that we created (above)
        banter_context["critic_1_chat"].append(u1)
        #   Save the critic/assistant response that we just got
        banter_context["critic_1_chat"].append(a1)
        banter_context["critic_1_ready"] = True
        #print_server_log(f"'{c1_name}' response:\n{message}",
        #                "user_banter_chat_request()",
        #                MODULE_LLM_DEBUG)
    else:
        prior = c1_api.getPriorRequests()[0]
        print_server_log(f"On '{c1_name}'\nERROR:\n{json.dumps(prior['error'],indent=4)}",
                        "user_banter_chat_request()",
                        MODULE_LLM_DEBUG)
    #
    #   Get response for critic 2
    #
    c2_resp = c2_api.nextResponse()
    if c2_resp:
        resp_dict = c2_resp.json()
        a2 = ChatMessage()
        message = resp_dict['choices'][0]['message']
        a2.setMessage(message)
        a2.setName(f"UserBanter_Response_{c2_name}")
        #   Save the critic response and mark that there is a critic comment ready
        #   Save the user message that we created (above)
        banter_context["critic_2_chat"].append(u2)
        #   Save the critic response/assistant that we just got
        banter_context["critic_2_chat"].append(a2)
        banter_context["critic_2_ready"] = True
        #print_server_log(f"'{c2_name}' response:\n{message}",
        #                "user_banter_chat_request()",
        #                MODULE_LLM_DEBUG)
    else:
        prior = c2_api.getPriorRequests()[0]
        print_server_log(f"On '{c2_name}'\nERROR:\n{json.dumps(prior['error'],indent=4)}",
                        "user_banter_chat_request()",
                        MODULE_LLM_DEBUG)
    
    #
    #   Stop and clean up after the threads - so they don't keep running
    c1_api.terminateThread()
    c2_api.terminateThread()
    return



