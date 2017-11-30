import json, requests
from bs4 import BeautifulSoup
import itertools
import pprint
import pickle
import os.path
import inflect

def _get(BASE_URL, path, params=None, headers=None):
    # BASE_URL = "https://api.genius.com"
    secret_key = get_secret_key()
    headers = {'Authorization':secret_key}
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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_lyrics_from_song_path(song_path):
    p = inflect.engine()
    data = _get(BASE_URL = "https://genius.com", path=song_path[1:])
    soup = BeautifulSoup(data.content, "html5lib")
    song_title = soup.find_all("h1",class_="header_with_cover_art-primary_info-title")[0].get_text()
    words_with_tags = soup.find_all("div",class_="lyrics")
    words = BeautifulSoup(str(words_with_tags[0]),"html5lib").get_text().split('\n')
    words = [line.strip().lower() for line in words if len(line)>0]
    words_clean = []
    for line in words:
        temp_list = []
        list_of_words = line.split(' ')
        for word in list_of_words:
            if not is_number(word):
                temp_list.append(word)
            else:
                temp_list.append(p.number_to_words(word))
        words_clean.append(" ".join(temp_list))
    return song_title, words_clean

def compare(song_1,song_2):
    try:
        matched_lines = [i for i in song_1['song_lyrics'] if i in song_2['song_lyrics']]
    except KeyError:
        import ipdb; ipdb.set_trace()
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
        dict_out['matched_lines'] = set(matched_lines_clean)
        return dict_out
    else:
        return None

def get_secret_key():
    with open('secret_key.txt', 'r') as myfile:
        secret_key=myfile.read().replace('\n', '')
    return secret_key

def get_artist_id():
    BASE_URL = "https://api.genius.com"
    search_url = BASE_URL + "/search"
    song_title = "Don't swallow the cap"
    params = {'q': song_title}
    secret_key = get_secret_key()
    headers = {'Authorization':secret_key}
    response = requests.get(search_url, params=params, headers=headers)
    song_data = json.loads(response.text)
    artist_api_path = song_data['response']['hits'][0]['result']['primary_artist']['api_path']
    artist_id = artist_api_path.split('/')[-1]
    return artist_id

def save_list_of_song_paths(itemlist):
    with open('list_of_song_paths', 'wb') as fp:
        pickle.dump(itemlist, fp)

def get_song_lyrics(song_path):
    temp_dict = {}
    if song_path.split('-')[-2] != 'live':
        if song_path.split('-')[-2] != 'version':
            if song_path.split('-')[-2] != 'demo':
                if song_path.split('-')[-2] != 'remix':
                    print(song_path)
                    song_title, song_lyrics = get_lyrics_from_song_path(song_path)
                    temp_dict['song_title'] = song_title
                    temp_dict['song_lyrics'] = song_lyrics
                    # song_list_of_dicts.append(temp_dict)
                    # print("processed {} of {} songs".format(count,len(list_of_song_paths)))
                    # count += 1
    return temp_dict

def song_loop(list_of_song_paths):
    song_list_of_dicts = []
    for song_path in list_of_song_paths:
        song_list_of_dicts.append(get_song_lyrics(song_path))
    return song_list_of_dicts

def save_song_lyrics(song_list_of_dicts):
    with open('all_song_lyrics.json', 'w') as fout:
        json.dump(song_list_of_dicts, fout)

def compare_lyrics_to_other_songs(song_list_of_dicts):
    for a, b in itertools.combinations(song_list_of_dicts, 2):
        if bool(a) and bool(b):
            matched_lines_between_songs = compare(a,b)
            if matched_lines_between_songs:
                pprint.pprint(matched_lines_between_songs)

if not os.path.isfile('all_song_lyrics.json'):
    if not os.path.isfile('list_of_song_paths'):
        artist_id = get_artist_id()
        list_of_song_paths = get_artist_song_paths(artist_id)
        save_list_of_song_paths(list_of_song_paths)
    else:
        with open ('list_of_song_paths', 'rb') as fp:
            list_of_song_paths = pickle.load(fp)
    song_list_of_dicts = song_loop(list_of_song_paths)
    save_song_lyrics(song_list_of_dicts)
else:
    song_list_of_dicts = json.load(open('all_song_lyrics.json'))
compare_lyrics_to_other_songs(song_list_of_dicts)
