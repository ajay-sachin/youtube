This is a simple streamlit dashboard, which analyses each video.

I have scrapped the YouTube data using YouTube API.

Data Scrapped: Three Channels( Chennai Super Kings, Mumbai Indians, Royal Challengers Bangalore) recent 10 videos from each channel with their subscribers, channel ID, channel published date, views, thumbnail, playlist ID, are extracted.

From each video, viewCount, likeCount, video ID, description, comments with commentators name, no of comments, video title, and thumbnails are extracted.

Connection established to MongoDB Database to store information as .csv format in the cluster.
Data Scrapping of the youtube in .ipynb also added.
