import json
import requests
import time


access_token = 'eae371614830f5cb881faced0f94583e866c4b0bb28b5dde25bac8a1e43553a\
446deb834bd3eb86e70563'
group_id = 'lovedonnu_ua'


class VKException(Exception):

    '''Данные исключения должны возбуждаться только при корректных ответах от
    сервера vk на запросы, но если в ответе есть сообщение об ошибке.

    Сообщения должны подробно описывать действие, которое привело к исключению.
    '''

    def __init__(self, message):
        self.message = message
        self.error_msg = error_msg
        self.error_code = error_code

    def __str__(self):
        return self.message

    def get_msg_and_code():
        return (self.error_msg, self.error_code)


class UserDeactivatedException(VKException):

    '''docstring for UserDeactivExceptionated
    '''

    def __init__(self, message, error_msg, error_code, user_id):
        self.message = message
        self.error_msg = error_msg
        self.error_code = error_code
        self.user_id = user_id

    def get_user_id(self):
        return self.user_id


class GraphException(Exception):

    '''Документация
    '''

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class NotConnectedException(GraphException):

    '''Документация
    '''
    pass


def get_friends_list(user_id, access_token=''):
    '''Функция принимает ID человека вконтакте и возвращает список его друзей.
    Параметр user_id является обязательным, параметр access_token не является
    обязатеньным. При передаче access_token список друзей возвращается в
    порядке рейтинга, если access_token дает соответствующее разрешение для
    переданного user_id.

    В случае, если сервер vk вернул ответ с ошибкой, возбуждается VKException
    с ее описанием.
    Если страница запрашиваемого пользователя удалена, возбуждается VKException
    с соответствующим сообщением.'''

    if access_token == '':
        try:
            request = requests.get('https://api.vk.com/method/friends.get?' +
                                   'v=5.37&user_id=' + str(user_id))
        except Exception as error:
            print(error, 'in request with access_token.')
            raise Exception
    else:
        try:
            # Здесь достаточно сделать один запрос - он вернет всех друзей.
            request = requests.get('https://api.vk.com/method/friends.get?' +
                                   'v=5.37&order=hints&user_id=' +
                                   str(user_id) + '&access_token='
                                   + access_token)
        except Exception as error:
            print(error, 'in request without access_token.')
            raise Exception

    if 'error' in request.json().keys():
        if request.json()['error']['error_msg'] == \
                'Access denied: user deactivated':
            raise VKException('user deactivated')
        raise VKException('VK error: %s Error code: %s'
                          % (request['error']['error_msg'],
                             request['error']['error_code']))

    friends_list = request.json()['response']['items']
    return friends_list


def get_members_list(group_id):
    '''Функция принимает ID паблика вконтакте и возвращает список подписчиков.

    В случае, если сервер vk вернул ответ с ошибкой, возбуждается VKException
    с ее описанием.'''

    try:
        request = requests.get('https://api.vk.com/method/groups.getMembers?' +
                               'v=5.37&group_id=' + str(group_id))
    except Exception as error:
        print(error, 'in first get request.')
        raise Exception

    if 'error' in request.json().keys():
        raise VKException('VK error: %s Error code: %s'
                          % (request['error']['error_msg'],
                             request['error']['error_code']))

    counts = request.json().get('response').get('count')
    members_list = request.json().get('response').get('items')

    for offset in range(1000, counts, 1000):
        # TODO: реализовать механизм повторного запроса при исключении.
        try:
            request = requests.get('https://api.vk.com/method/' +
                                   'groups.getMembers?' +
                                   'v=5.37&' +
                                   'group_id=' + group_id +
                                   '&offset=' + str(offset))
            members_list.extend(request.json()['response']['items'])
        except Exception as error:
            print('Exception', error, 'in get with offset request.')
            raise Exception

    return members_list


def save_to_file(filename, structure, extension='friends'):
    '''Функция создает файл с именем filename и сохраняет в него переданную ей
    структуру structure в формате json.

    Параметр extension не является обязательным, однако рекомендуется задавать
    его следующим образом:

    полный список друзей: задание не требуется (по умолчанию)
    отфильтрованный список друзей: filtered-friends
    полный список подписчиков: members
    отфильтрованный список подписчиков: filtered-members
    полный словарь связей: graph-dict
    отфильтрованный словарь связей: filtered-graph-dict

    Для удобства просмотра файлов в текстовом редакторе, автоматически
    устанавливается расширение json.'''

    file = open(filename + '.' + extension + '.json', 'w')
    file.write(json.dumps(structure, sort_keys=True, indent=4))
    file.close()


def load_all_from_files(directory=''):
    pass


def get_friends_lists_for_group(members_list):
    '''Функция принимает список подписчиков и возвращает словарь вида
    "ID подписчика": [список его друзей].'''

    done_dict = {}

    while (len(done_dict) < len(members_list)):

        undone_list = [user for user in members_list
                       if str(user) not in done_dict.keys()]
        print('Debug: created new undone list with', len(undone_list),
              'entries.')

        for user in undone_list:
            time.sleep(0.335)
            try:
                current_user_friends = get_friends_list(user)
                done_dict[str(user)] = current_user_friends
                print('Debug:', str(user),
                      'friends list is added to dictionary. [' +
                      str(len(done_dict)) + '/' +
                      str(len(members_list)) + ']')
            except VKException as error:
                if error.message == 'user deactivated':
                    done_dict[str(user)] = 'DEACTIVATED'
                    print('Deactivated user:', str(user))
                else:
                    print('VK Error', error.message, 'for', str(user))
            except Exception as error:
                print('Non-VK exception for user', str(user), '-', str(error))

    print('Debug: DONED.')
    return done_dict


def filter_friends_lists(full_dictionary):
    '''Функция принимает словарь вида {"ID подписчика": [список его друзей]}
    и возвращает словарь аналогичного вида, в котором у каждого подписчика
    удалены друзья, которые не являются ключами словаря.'''

    filtered_dictionary = {}

    deactivated_users = []

    active_users = {user: full_dictionary[user]
                    for user in full_dictionary.keys()
                    if full_dictionary[user] != "DEACTIVATED"}

    for user in active_users.keys():
        user_friends_list = []
        for friend in active_users[user]:
            if str(friend) in active_users.keys():
                user_friends_list.append(friend)
        filtered_dictionary[user] = user_friends_list

    return filtered_dictionary


def generate_connected_component(users_set, graph):
    '''Функция принимает множество пользователей и граф, а возвращает
    порожденную    компоненту связности (если все пользователи переданного
    множества сами находятся в одной компоненте).
    Если же в переданном множестве
    содержатся пользователи из различных компонент, то будет возвращено
    объединение порожденных ими компонент связности.

    Рекомендуемый вариант использования - передача множества из одного 
    пользователя.'''

    component = users_set
    previos_component = set()

    while len(previos_component) < len(component):
        difference = component.difference(previos_component)
        previos_component = component.copy()

        for user in difference:
            if str(user) not in graph.keys():
                continue
            else:
                component.update(set(graph[str(user)]))

    return component


file = open('studrada.filtered-graph-dict.json', 'r')
graph = json.loads(file.read())


def get_distance(start_user, end_user, graph):
    ''' Функция принимает две вершины графа, а возвращает расстояние между ними.
    В случае, если вершины в разных компонентах связности, или таких вершин нет
    в графе, порождаются соответствующие исключения.'''


    if end_user not in generate_connected_component({start_user}, graph):
        raise GraphException('Not in one connected component.')

    if (str(start_user) not in graph.keys()) or \
        (str(end_user) not in graph.keys()):
        raise GraphException('Not in graph.')

    environment = {start_user}

    distance = 0

    while end_user not in environment:
        distance += 1
        previos_environment = environment.copy()
        for user in previos_environment:
            environment.update(set(graph[str(user)]))

    return distance

##########################################################################



