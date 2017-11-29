import json, requests
from bs4 import BeautifulSoup
import itertools
import pprint

def _get(BASE_URL, path, params=None, headers = {'Authorization':
           'Bearer b5kj3f2puoH_u3O5EFxfw-hxUOb_ImINLx-wr_knQitzkKEFdeFVFhbTsGKS7etH'}):
    # BASE_URL = "https://api.genius.com"
    requrl = '/'.join([BASE_URL, path])
    response = requests.get(url=requrl, params=params, headers=headers)
    response.raise_for_status()
    try:
        return response.json()
    except:
        return response

def get_artist_song_paths(artist_id):
    # initialize variables & a list.
    current_page = 1
    next_page = True
    songs = []
    # main loop
    while next_page:
        path = "artists/{}/songs/".format(artist_id)
        params = {'page': current_page}
        data = _get(BASE_URL = "https://api.genius.com", path=path, params=params)
        page_songs = data['response']['songs']
        if page_songs:
            songs += page_songs
            current_page += 1
        else:
            next_page = False
    # get all the song ids, excluding not-primary-artist songs.
    list_of_songs_paths = []
    for song in songs:
        if str(song['primary_artist']['id']) == artist_id:
            list_of_songs_paths.append(song['path'])

    return list_of_songs_paths

def get_lyrics_from_song_path(song_path):
    data = _get(BASE_URL = "https://genius.com", path=song_path[1:])
    soup = BeautifulSoup(data.content, "html5lib")
    song_title = soup.find_all("h1",class_="header_with_cover_art-primary_info-title")[0].get_text()
    words_with_tags = soup.find_all("div",class_="lyrics")
    words = BeautifulSoup(str(words_with_tags[0]),"html5lib").get_text().split('\n')
    return song_title, words

def compare(song_1,song_2):
    matched_lines = [i for i in song_1['song_lyrics'] if i in song_2['song_lyrics']]
    matched_lines_clean = []
    for line in matched_lines:
        if len(line) > 0:
            if not line.isspace():
                if not '[' in line or not ']' in line:
                    matched_lines_clean.append(line)
    if matched_lines_clean:
        dict_out = {}
        dict_out['song1_title'] = song_1['song_title']
        dict_out['song2_title'] = song_2['song_title']
        dict_out['matched_lines'] = matched_lines_clean
        return dict_out
    else:
        return None


BASE_URL = "https://api.genius.com"
search_url = BASE_URL + "/search"
song_title = "Don't swallow the cap"
params = {'q': song_title}
headers = {'Authorization':
           'Bearer b5kj3f2puoH_u3O5EFxfw-hxUOb_ImINLx-wr_knQitzkKEFdeFVFhbTsGKS7etH'}
response = requests.get(search_url, params=params, headers=headers)
song_data = json.loads(response.text)
artist_api_path = song_data['response']['hits'][0]['result']['primary_artist']['api_path']
artist_id = artist_api_path.split('/')[-1]

list_of_song_paths = get_artist_song_paths(artist_id)

song_list_of_dicts = []
count = 0

for song_path in list_of_song_paths:
    temp_dict = {}
    if song_path.split('-')[-2] != 'live':
        if song_path.split('-')[-2] != 'version':
            if song_path.split('-')[-2] != 'demo':
                if song_path.split('-')[-2] != 'remix':
                    print(song_path)
                    song_title, song_lyrics = get_lyrics_from_song_path(song_path)
                    temp_dict['song_title'] = song_title
                    temp_dict['song_lyrics'] = song_lyrics
                    song_list_of_dicts.append(temp_dict)
                    print("processed {} of {} songs".format(count,len(list_of_song_paths)))
                    count += 1

for a, b in itertools.combinations(song_list_of_dicts, 2):
    matched_lines_between_songs = compare(a,b)
    if a['song_title'] == 'Wake Up Your Saints' and a['song_title'] == 'Anyone''s Ghost' or b['song_title'] == 'Wake Up Your Saints' and a['song_title'] == 'Anyone''s Ghost':
        import ipdb; ipdb.set_trace()

    if matched_lines_between_songs:
        pprint.pprint(matched_lines_between_songs)
