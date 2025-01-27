from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime, timezone
import os
import isodate

load_dotenv()

class YouTubeDataFetcher:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def _extract_channel_identifier(self, url):
        if '@' in url:
            handle = url.split('@')[1].split('/')[0]
            return 'forHandle', '@' + handle
        elif '/channel/' in url:
            channel_id = url.split('/channel/')[1].split('/')[0] #spilliting the url for getting channel
            return 'id', channel_id
        elif '/user/' in url:
            username = url.split('/user/')[1].split('/')[0] #spilliting the url for getting username
            return 'forUsername', username
        elif '/c/' in url:
            custom_name = url.split('/c/')[1].split('/')[0] ##spilliting the url for getting custom name
            return 'forUsername', custom_name
        else:
            raise ValueError("Unsupported URL format")

    def get_channel_details(self, channel_url):
        try:
            filter_type, identifier = self._extract_channel_identifier(channel_url)
            
            # getting channel details
            channel_request = self.youtube.channels().list(
                part="snippet,statistics,brandingSettings,contentDetails,status",
                **{filter_type: identifier}
            )
            channel_response = channel_request.execute()
            
            if not channel_response.get('items'):
                print("No channel found")
                return None
                
            channel = channel_response['items'][0]
            channel_id = channel['id']
            
            # last activities
            activities_request = self.youtube.activities().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=4
            )
            activities_response = activities_request.execute()
            
            recent_activities = []
            for activity in activities_response.get('items', []):
                recent_activities.append({
                    'type': activity['snippet']['type'],
                    'title': activity['snippet']['title'],
                    'published_at': self._format_date(activity['snippet']['publishedAt'])
                })
            
            # channel information
            channel_info = {
                # Basic Information
                'name': channel['snippet']['title'],
                'channel_id': channel_id,
                'custom_url': f"https://youtube.com/{channel['snippet'].get('customUrl', '')}",
                
                # Contact Information
                'email': self._extract_email(channel['snippet'].get('description', '')),
                'country': channel['snippet'].get('country', 'Not specified'),
                'social_links': self._extract_social_links(channel['snippet'].get('description', '')),
                
                # Statistics
                'subscriber_count': "{:,}".format(int(channel['statistics'].get('subscriberCount', '0'))),
                'video_count': "{:,}".format(int(channel['statistics'].get('videoCount', '0'))),
                'view_count': "{:,}".format(int(channel['statistics'].get('viewCount', '0'))),
                
                # Dates
                'joined_date': self._format_date(channel['snippet']['publishedAt']),
                
                # Recent Activities
                'recent_activities': recent_activities
            }
            
            return channel_info
            
        except Exception as e:
            print(f"Error fetching channel details: {e}")
            return None
    

    def _extract_social_links(self, description):
        import re
        social_patterns = {
            'Instagram': r'instagram\.com/[a-zA-Z0-9._]+',
            'Twitter': r'twitter\.com/[a-zA-Z0-9._]+',
            'Facebook': r'facebook\.com/[a-zA-Z0-9._]+',
            'LinkedIn': r'linkedin\.com/[a-zA-Z0-9._/-]+',
            'Website': r'https?://(?!youtube\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?'
        }
        
        social_links = {}
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, description)
            if matches:
                social_links[platform] = matches[0] 
        return social_links

    def _format_date(self, date_string):
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date.strftime('%B %d, %Y')

def main():
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("Please set YOUTUBE_API_KEY environment variable")
        return

    fetcher = YouTubeDataFetcher(api_key)
    

    channel_url = "https://www.youtube.com/@bentech_ds"
    
    print("\nFetching channel details...")
    channel_info = fetcher.get_channel_details(channel_url)
    
    if channel_info:
        print("\n📊 Channel Information:")
        print(f"📌 Name: {channel_info['name']}")
        print(f"🔗 Custom URL: {channel_info['custom_url']}")
        print(f"📍 Country: {channel_info['country']}")
        
        if channel_info['email']:
            print(f"📧 Email: {channel_info['email']}")
        
        print(f"\n📈 Channel Statistics:")
        print(f"👥 Subscribers: {channel_info['subscriber_count']}")
        print(f"🎥 Total Videos: {channel_info['video_count']}")
        print(f"👀 Total Views: {channel_info['view_count']}")
        print(f"📅 Joined: {channel_info['joined_date']}")
        
        if channel_info['social_links']:
            print("\n🌐 Social Links:")
            for platform, link in channel_info['social_links'].items():
                print(f"{platform}: {link}")
        
        if channel_info['recent_activities']:
            print("\n🔄 Recent Activities:")
            for activity in channel_info['recent_activities']:
                print(f"\n📌 {activity['type'].title()}")
                print(f"   {activity['title']}")
                print(f"   Posted on: {activity['published_at']}")

if __name__ == "__main__":
    main()