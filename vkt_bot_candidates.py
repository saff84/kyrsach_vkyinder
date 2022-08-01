import requests
import time


class VkRequest:
    url_base = 'https://api.vk.com/method/'

    def __init__(self, token, vk_version):
        self.params = {
            'access_token': token,
            'v': vk_version
        }

    def database_getCities(self, city_name):
        """Получает список идентификаторов городов"""
        method = 'database.getCities'
        database_getCities_url = self.url_base + method
        # city_name = city_name.title()
        database_getCities_params = {
            'country_id': 1,
            'q': city_name,
            'count': 1
        }
        print('________', database_getCities_params)
        res = requests.get(database_getCities_url, params={**self.params, **database_getCities_params}).json()
        if res['response']['count'] and res['response']['items'][0]['title'].lower() == city_name.lower():
            print(res['response']['items'][0])
            return res['response']['items'][0]['id'], res['response']['items'][0]['title']
        else:
            return None

    def users_search(self, skip_id={}, **kwargs) -> list:
        """Формирует список словарей
            [{'vk_id': id, 'first_name': first_name, 'last_name': last_name, 'bdate': bdate}] кандидатов"""
        method = 'users.search'
        users_search_url = self.url_base + method
        users_search_params = {
            'has_photo': 1,
            'status': 6,
            'count': 10,
            'offset': 0,
            'fields': 'bdate',
            **kwargs
        }
        res = requests.get(users_search_url, params={**self.params, **users_search_params}).json()
        print('count=', res['response']['count'])
        candidates = []
        for item in res['response']['items']:
            if not item['is_closed'] and 'bdate' in item and item['id'] not in skip_id:
                photos = self.get_photos(item['id'])
                candidates.append({"vk_id": item['id'],
                                   "first_name": item['first_name'],
                                   "last_name": item['last_name'],
                                   "bdate": item['bdate'],
                                   **photos
                                   })
                time.sleep(0.25)
        # pprint(candidates[:1])
        return candidates

    def get_photos(self, id) -> dict:
        method = 'photos.get'
        get_photos_url = self.url_base + method
        get_photos_params = {
            'owner_id': id,
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1,
            'count': 300
        }
        res = requests.get(get_photos_url, params={**self.params, **get_photos_params}).json()
        print(id)
        # если не нашли/мало нашли в альбоме 'profile', ищем в 'wall'
        photo_list = res['response']['items']
        if res['response']['count'] < 3 and get_photos_params['album_id'] == 'profile':
            get_photos_params['album_id'] = 'wall'
            res2 = requests.get(get_photos_url, params={**self.params, **get_photos_params}).json()
            photo_list += res2['response']['items']
        photos = {'attach': ','.join([f"photo{p['owner_id']}_{p['id']}" \
                                      for p in sorted(photo_list, key=lambda d: d['likes']['count'], reverse=True)][
                                     :3])}
        return photos
