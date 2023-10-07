import numpy as np
import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from pymongo import MongoClient
import csv

api_key = "AIzaSyABi2XonLSZIeHvo35TDZhO7UgHpsXWrts"
channel_id = ['UCl23mvQ3321L7zO6JyzhVmg',  #mumbai_indians
              'UC2J_VKrAzOEJuQvFFtj3KUw',  #chennai_super_kings
              'UCCq1xDJMBRF61kiOgU90_kw',  #royal_challengers_bangalore
]
youtube = build('youtube', 'v3', developerKey=api_key)

def get_channel_info(youtube, channel_id):
  all_data= []
  request = youtube.channels().list(
      part='snippet, content_details, statistics',
      id = ','.join(channel_id))
  response = request.execute()
  for i in range(len(response['items'])):
        data = dict(channelName = response['items'][i]['snippet']['title'],
                    description = response['items'][i]['snippet']['description'],
                    publishdate = response['items'][i]['snippet']['publishedAt'],
                    subscribers = response['items'][i]['statistics']['subscriberCount'],
                    views = response['items'][i]['statistics']['viewCount'],
                    totalVideos = response['items'][i]['statistics']['videoCount'],
                    playlistId = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'],
                    thumbnail =  response['items'][i]['snippet']['thumbnails']['high']['url']
                    )
        all_data.append(data)
  return pd.DataFrame(all_data)

channel_data = get_channel_info(youtube, channel_id)
numerical_cols = ['subscribers', 'views', 'totalVideos']
channel_data[numerical_cols] = channel_data[numerical_cols].apply(pd.to_numeric, errors='coerce')

def get_video_ids(youtube, playlist_id):

    request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId = playlist_id,
                maxResults = 50)
    response = request.execute()

    video_ids = []

    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    more_pages = True

    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(
                        part='contentDetails',
                        playlistId = playlist_id,
                        maxResults = 50,
                        pageToken = next_page_token)
            response = request.execute()

            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')

    return video_ids[:10] #getting 10 videos...

def get_video_details(youtube, video_ids):

    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()

        for video in response['items']:
            stats_to_keep = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                             'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                             'contentDetails': ['duration', 'definition', 'caption']
                            }
            video_info = {}
            video_info['video_id'] = video['id']

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try:
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)
    return all_video_info

video_df = pd.DataFrame()
#comments_df = pd.DataFrame()

for c in channel_data['channelName'].unique():

    print("Getting video information from channel: " + c)
    playlist_id = channel_data.loc[channel_data['channelName']== c, 'playlistId'].iloc[0]
    video_ids = get_video_ids(youtube, playlist_id)

    # get video data
    video_data = get_video_details(youtube, video_ids)
    # get comment data
    #comments_data = get_comments_in_videos(youtube, video_ids)

    # append video data together and comment data toghether

    video_df = video_df.append(video_data)
    #comments_df = comments_df.append(comments_data, ignore_index=True)

cols = ['viewCount', 'likeCount', 'favouriteCount', 'commentCount']
video_df[cols] = video_df[cols].apply(pd.to_numeric, errors='coerce', axis=1)
video_df.to_csv('videos.csv')

def get_comments_in_videos(youtube, video_ids):
    all_comments = []

    for video_id in video_ids:
        data = youtube.commentThreads().list(
            part='snippet,replies',
            videoId=video_id,
            maxResults='100',
            textFormat="plainText").execute()

        for i in data["items"]:
            commentsData = dict(

            name = i["snippet"]['topLevelComment']["snippet"]["authorDisplayName"],
            comment = i["snippet"]['topLevelComment']["snippet"]["textDisplay"],
            published_at = i["snippet"]['topLevelComment']["snippet"]['publishedAt'],
            likes = i["snippet"]['topLevelComment']["snippet"]['likeCount'],
            replies = i["snippet"]['totalReplyCount'])

            all_comments.append(commentsData)

            totalReplyCount = i["snippet"]['totalReplyCount']

            if totalReplyCount > 0:

                parent = i["snippet"]['topLevelComment']["id"]

                data2 = youtube.comments().list(part='snippet', maxResults='100', parentId=parent,
                                                textFormat="plainText").execute()

                for i in data2["items"]:
                    commentsData = dict(
                    name = i["snippet"]["authorDisplayName"],
                    comment = i["snippet"]["textDisplay"],
                    published_at = i["snippet"]['publishedAt'],
                    likes = i["snippet"]['likeCount'],
                    replies = "")

                    all_comments.append(commentsData)

        while ("nextPageToken" in data):

            data = youtube.commentThreads().list(part='snippet', videoId=video_id, pageToken=data["nextPageToken"],
                                                maxResults='100', textFormat="plainText").execute()

            for i in data["items"]:
                commentsData = dict(
                name = i["snippet"]['topLevelComment']["snippet"]["authorDisplayName"],
                comment = i["snippet"]['topLevelComment']["snippet"]["textDisplay"],
                published_at = i["snippet"]['topLevelComment']["snippet"]['publishedAt'],
                likes = i["snippet"]['topLevelComment']["snippet"]['likeCount'],
                replies = i["snippet"]['totalReplyCount'])

                all_comments.append(commentsData)

                totalReplyCount = i["snippet"]['totalReplyCount']

                if totalReplyCount > 0:

                    parent = i["snippet"]['topLevelComment']["id"]

                    data2 = youtube.comments().list(part='snippet', maxResults='100', parentId=parent,
                                                    textFormat="plainText").execute()

                    for i in data2["items"]:
                        commentsData = dict(
                        name = i["snippet"]["authorDisplayName"],
                        comment = i["snippet"]["textDisplay"],
                        published_at = i["snippet"]['publishedAt'],
                        likes = i["snippet"]['likeCount'],
                        replies = '')

                        all_comments.append(commentsData)

    return all_comments

comments_df = pd.DataFrame()

for c in channel_data['channelName'].unique():

    print("Getting video information from channel: " + c)
    playlist_id = channel_data.loc[channel_data['channelName']== c, 'playlistId'].iloc[0]
    video_ids = get_video_ids(youtube, playlist_id)

    # get video data

    # get comment data
    comments_data = get_comments_in_videos(youtube, video_ids)

    # append video data together and comment data toghether
    comments_df = comments_df.append(comments_data, ignore_index=True)

#convert to csv format
comments_df.to_csv('comments.csv')
channel_data.to_csv('channel_data.csv')

#open the csv file
csvfile1=open('channel_data.csv','r')
csvfile2=open('comments.csv','r')
csvfile3=open('videos.csv','r')

#read the csv file
reader1 = csv.DictReader( csvfile1 )
reader2 = csv.DictReader( csvfile2 )
reader3 = csv.DictReader( csvfile3 )

mongo_client=MongoClient() 
db=mongo_client.cluster0
db.segment.drop()

header1 = ['channelName','description','publishdate','subscribers','views','totalVideos','playlistId','thumbnail']
header2 = ['name','comment','publish_at','likes','replies']
header3 = ['video_id','channelTitle','title','description','tags','publishedAt','viewCount','likeCount','favouriteCount','commentCount','duration','definition','caption']

for each in reader1:
    row1={}
    for field in header1:
        row1[field]=each[field]
 
    db.segment.insert(row1)

for each in reader2:
    row2={}
    for field in header2:
        row2[field]=each[field]
 
    db.segment.insert(row2)

for each in reader3:
    row3={}
    for field in header3:
        row3[field]=each[field]
 
    db.segment.insert(row3)



# create streamlit app
st.title("YouTube Channel Analyzer")

# Sidebar for user input
st.sidebar.header("Enter Channel ID")
channel_id = st.sidebar.selectbox("Select your channel", ["MumbaiIndians", "chennaiipl", "royalchallengersbangalore"])
#channel_id = st.selectbox("Select your channel", ["MumbaiIndians", "chennaiipl", "royalchallengersbangalore"])
st.write("Selected channel:", channel_id)


if st.sidebar.button("Analyze"):
    if channel_id:
        channel_info = get_channel_info(youtube,channel_id)
        if channel_info:
            st.header(f"Channel: {channel_info['snippet']['title']}")
            st.subheader("Channel Statistics:")
            st.write(f"Total Subscribers: {channel_info['statistics']['subscriberCount']}")
            st.write(f"Total Videos: {channel_info['statistics']['videoCount']}")
            st.write(f"Total Views: {channel_info['statistics']['viewCount']}")
        else:
            st.warning("Channel not found. Please check the Channel ID.")
    else:
        st.warning("Please enter a valid Channel ID.")

# Add a footer
st.text("Powered by YouTube Data API")

# Run the app
if __name__ == '__main__':
    st.text('Click to analyze')
