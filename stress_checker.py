#!/usr/bin/env python

import urllib2
import os, glob
import json
import datetime
import time
import sys
import getopt

from multiprocessing import Pool

#Relative path of the json files which are to be read
path="jsonFiles/"
#Counter that keeps track of the number of files scanned so far
files_scanned=-1
#Counter that keeps tracks of the number of API requests made so far
api_requests=0
#Maximum number of API requests for the stress checker.  Enter '-1' for no limitations.
max_requests=-1
#Total time taken across all API calls
total_time=datetime.datetime.now()
#Dictionary data structure to store the statistics(time taken) for API calls 
statsDict=[]
# Number of concurrent requests (ie. thread pool size)
concurrent_requests = 5
#Maintains the beginning time to maintain the average number of API calls made per second
beginning_time=datetime.datetime.now()
#Maintains the number of API requests made in the current second
current_requests=0
#Demo API Key.  We will use this API key to perform the stress tests
#API_KEY='2EvC9SVR0Y5vBt48dA1xMwkAxv8XP15OZ7ulsw'
API_KEY='Q7E5Zj3q5WDlOg2dToY8bQMmN01ynybCqcIZjg'
#simple flag used to check if it's the first time that we're entering compile_statistics program
flag=0


# Method that writes the statistics to files.  Here, two files are created - one is a json file that stores the exact time taken per request.  The other is a simple .txt file that prints the overall results
def write_statistics_to_file(api_requests, total_time):
    global statsDict
    stats_filename="statistics/statistics"+str(files_scanned/10)+".json"
    statsWrite=open(stats_filename, 'w')
    statsWrite.write(json.dumps(statsDict, indent=4))
    statsDict=[]
    sh_statsWrite=open("short_statistics.txt", 'w')
    sh_statsWrite.write("Total API calls made: " + str(api_requests))
    sh_statsWrite.write("\nTotal time taken: " + str(datetime.datetime.now() - beginning_time))
    sh_statsWrite.write("\nAverage time taken per API call" + str((datetime.datetime.now() - beginning_time)/api_requests))
    statsWrite.close()
    sh_statsWrite.close()

# Method that stores the statistics in a dictionary and appends that dictionary entry into an array that will later be written into a json formatted file
def compile_statistics(time_taken, url, tagSplit):
    global total_time
    global flag
    
    if flag==0:
        total_time=time_taken
    else:
        total_time+=time_taken
    
    flag=1
    stats={}
    stats["url"]=url
    stats["tags"]=tagSplit
    stats["time"]=str(time_taken)
    global statsDict
    statsDict.append(stats)
    

# Takes a valid API call URL and returns the response as a string 
def get_enriched_data(apiUrl):
    try:
        start_time = datetime.datetime.now()
        searchPage = urllib2.urlopen(apiUrl)
        end_time = datetime.datetime.now()
    except IOError:
        print "An IOError Exception was raised"
        print "API Call URL: " + apiUrl
        print "Ignoring... and... trying a new URL"
        return "", 0
    else:
        enriched_data=json.load(searchPage)
        return enriched_data, (end_time-start_time)
    

# Takes in a set of tags and constructs the API call URL.
def get_api_url(tagSplit):
    queryString=""
    for tag in tagSplit:
        if (queryString==""):
            queryString+=tag
        else:
            queryString+=", " + tag
    
    if queryString !="":
        try:
            queryString.decode('ascii')
        except UnicodeDecodeError:
            return 0
        else:
            queryString = urllib2.quote(queryString)
            pageUrl="http://dev-api.bueda.com/enriched?apikey="+API_KEY+"&tags="+queryString
            return pageUrl

    return 0


# Takes in the name of a json file and extracts the URL and set of tags corresponding to that URL.
# This function then calls 'get_enriched_data' that returns the contents of the API call and writes it to the results file. 
def read_json_file(json_filename):
    json_file = open(json_filename, 'r')
    
    global fileWrite
    global api_requests
    global current_requests
    
    for line in json_file:
        if "\"url\": " in line:
            urlSplit=line.split("\"url\": ")
            urlSplit=urlSplit[1].split("\"")
            url=urlSplit[1]
            
        
        if "\"tags\": " in line:
            tagSplit=line.split("\"tags\": ")
            tagSplit=tagSplit[1].split(", ")
                  
            tagSplit[0]=tagSplit[0].replace("\"", "", 1)   #Removing ' " ' in first tag
            tagSplit[-1]=tagSplit[-1].replace("\"", "")     #Removing ' " ' in last tag
            tagSplit[-1]=tagSplit[-1].replace("\r", "")     #Removing any newlines at the end of the tag
            tagSplit[-1]=tagSplit[-1].replace("\n", "")

            # Constructing API Call URL with the list of tags
            api_url=get_api_url(tagSplit)
            
            if (api_url!=0):    
                request_queue.append(api_url)
                    
                api_requests += 1
                if (api_requests==max_requests):
                    return 0
    return 1

def make_request(api_url):
    enriched_data, time_taken=get_enriched_data(api_url)

def usage():
    print "Default parameters are: \n path=\"/jsonFiles\" \n maximum API requests=NO LIMIT  \n API Requests per second= As many as possible"
    print "-h, --help for help"
    print "-p, --path to set the path where the json files are stored.  Default directory is /jsonFiles"
    print "-m, --max  to set the maximum number of API requests made.  Default is NO LIMIT.  Takes in an integer value."
    print "-c, --concurrent  to set the number of API requests to be in flight at a time. Default is 5.  Argument is an integer"
    
# This is the main function
argv=sys.argv[1:]
try:
    opts, args = getopt.getopt(argv, "p:m:c:h", ["help", "path=", "max", "concurrent"])
except getopt.GetoptError:
    usage()
    sys.exit()
for opt, arg in opts:
    if opt in ("-h", "--help"):
        usage()
        sys.exit()
    elif opt in ("-p", "path="):
        path=arg    
    elif opt in ("-m", "--max"):
        try:
            arg=int(arg)
        except ValueError:
            print "Enter an integer value!"
            usage()
            sys.exit()
        else:
            max_requests=int(arg)
            
    elif opt in ("-c", "--concurrent"):
        try:
            arg=int(arg)
        except ValueError:
            print "Enter an integer value!"
            usage()
            sys.exit()
        else:
            concurrent_requests=arg

if not os.path.exists("results"):
    os.makedirs("results")
if not os.path.exists("statistics"):
    os.makedirs("statistics")

    
request_queue = []
# This loops through all the .JSON files in the folder jsonFiles/ and then extracts
for json_filename in glob.glob( os.path.join(path, '*.json') ):
    print json_filename
    
    files_scanned+=1
    # Create a new file for every 10 Json files that have been scanned to avoid the file from getting too big
    #if (files_scanned%10==0):
        #write_filename="results/results"+ str(files_scanned/10)+".json"
        #if (files_scanned!=0):
        #    fileWrite.close()
        #    write_statistics_to_file(api_requests, total_time)
            
        #fileWrite= open(write_filename, 'w')
    
    # This means that we've reached our limit on the number of API calls.  So we break out of the loop and terminate the program
    if (read_json_file(json_filename)==0):
        break

pool = Pool(concurrent_requests)
result = pool.map(make_request, request_queue)

#fileWrite.close()
write_statistics_to_file(api_requests, total_time)
