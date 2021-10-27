from flask_rest_jsonapi import ResourceList, ResourceDetail
from .database import db
from .models import CSVFile
from .schema import AnalysisSchema, CSVSchema, PreviewSchema


class CSVDetail(ResourceDetail):
    schema = CSVSchema
    data_layer = {
        'session': db.session,
        'model': CSVFile
    }


class CSVList(ResourceList):
    schema = CSVSchema
    data_layer = {
        'session': db.session,
        'model': CSVFile,
    }


class CSVPreview(ResourceDetail):
    schema = PreviewSchema
    data_layer = {
        'session': db.session,
        'model': CSVFile
    }


class CSVAnalysis(ResourceDetail):
    schema = AnalysisSchema

    # def before_get_object(self, view_kwargs):
    #     if view_kwargs.get('column') is not None:
    #         try:
    #             computer = self.session.query(Computer).filter_by(id=view_kwargs['computer_id']).one()
    #         except NoResultFound:
    #             raise ObjectNotFound({'parameter': 'computer_id'},
    #                                  "Computer: {} not found".format(view_kwargs['computer_id']))
    #         else:
    #             if computer.person is not None:
    #                 view_kwargs['id'] = computer.person.id
    #             else:
    #                 view_kwargs['id'] = None

    data_layer = {'session': db.session,
                  'model': CSVFile,
                  # 'methods': {
                  #     'before_get_object': before_get_object
                  # }
                  }


# class CSVRelationship(ResourceRelationship):
#     schema = CSVSchema
#     data_layer = {
#         'session': db.session,
#         'model': CSVFile
#     }


# class UserRelationship(ResourceRelationship):
#     schema = UserSchema
#     data_layer = {
#         'session': db.session,
#         'model': User
#     }
#
#     @classmethod
#     def add_routes(cls, api):
#         api.route(cls, 'user_prompts', '/users/<int:id>/relationships/prompts')
#         api.route(cls, 'user_chats', '/users/<int:id>/relationships/chats')
#
#
# # might want to get public resources only for list endpoints
#
#
# class PromptList(ResourceList):
#     def query(self, view_kwargs):
#         return query_from_related(Prompt, self.session, view_kwargs, [User])
#
#     def before_create_object(self, data, view_kwargs):
#         if view_kwargs.get('user_id') is not None:
#             user = self.session.query(User).filter_by(id=view_kwargs['user_id']).one()
#             data['owner_id'] = user.id
#
#     schema = PromptSchema
#     data_layer = {
#         'session': db.session,
#         'model': Prompt,
#         'methods': {
#             'query': query,
#             'before_create_object': before_create_object,
#         }
#     }
#
#     @classmethod
#     def add_routes(cls, api):
#         api.route(cls,
#                   'prompt_list',
#                   '/prompts',
#                   '/users/<int:user_id>/prompts'
#                   )
#
#
# class PromptDetail(ResourceDetail):
#     def before_get_object(self, view_kwargs):
#         get_related(self.session, view_kwargs, [Chat], lambda obj: obj.prompt)
#
#     schema = PromptSchema
#     data_layer = {
#         'session': db.session,
#         'model': Prompt,
#         'methods': {
#             'before_get_object': before_get_object,
#         }
#     }
#
#     @classmethod
#     def add_routes(cls, api):
#         api.route(cls,
#                   'prompt_detail',
#                   '/prompts/<int:id>',
#                   '/chats/<int:chat_id>/prompt',
#                   )
#
#
# class PromptRelationship(ResourceRelationship):
#     schema = PromptSchema
#     data_layer = {
#         'session': db.session,
#         'model': Prompt
#     }
#
#     @classmethod
#     def add_routes(cls, api):
#         api.route(cls, 'prompt_user', '/prompts/<int:id>/relationships/owner')
#         api.route(cls, 'prompt_chats', '/prompts/<int:id>/relationships/chats')
#
#
# class ChatList(ResourceList):
#     def query(self, view_kwargs):
#         return query_from_related(Chat, self.session, view_kwargs, [User, Prompt])
#
#     def before_create_object(self, data, view_kwargs):
#         if view_kwargs.get('prompt_id') is not None:
#             prompt = self.session.query(Prompt).filter_by(id=view_kwargs['prompt_id']).one()
#             data['prompt_id'] = prompt.id
#
#     schema = ChatSchema
#     data_layer = {
#         'session': db.session,
#         'model': Chat,
#         'methods': {
#             'query': query,
#             'before_create_object': before_create_object,
#         }
#     }
#
#     @classmethod
#     def add_routes(cls, api):
#         api.route(cls,
#                   'chat_list',
#                   '/chats',
#                   '/users/<int:user_id>/chats',
#                   '/prompts/<int:prompt_id>/chats'
#                   )
#
#
# class ChatDetail(ResourceDetail):
#     def before_patch(self, *args, **kwargs):
#         """Make custom work here. View args and kwargs are provided as parameter"""
#
#         # we're only interested in patch requests with messages
#         if not kwargs['data'].get('messages'):
#             return
#
#         # if for some reason the last message comes from a bot, we don't need another reply
#         if kwargs['data']['messages'][-1]['bot']:
#             return
#
#         try:
#             chat_id = args[1]['id']
#             Chat.query.filter_by(id=chat_id).one()
#         except NoResultFound:
#             raise ObjectNotFound({'parameter': chat_id},
#                                  f'Chat: {chat_id} not found')
#         else:
#             chat = Chat.query.filter_by(id=chat_id).one()
#             reply = get_reply(
#                 chat.prompt,
#                 kwargs['data']['messages'],
#                 api_key = chat.owner.api_key,
#                 debug=True
#             )
#             kwargs['data']['messages'] += [{'bot': True, 'text': reply}]
#
#     schema = ChatSchema
#     data_layer = {
#         'session': db.session,
#         'model': Chat,
#         'methods': {
#             'before_patch': before_patch,
#         }
#     }
#
#     @classmethod
#     def add_routes(cls, api):
#         api.route(cls,
#                   'chat_detail',
#                   '/chats/<int:id>',
#                   )
#
#
# class ChatRelationship(ResourceRelationship):
#     schema = ChatSchema
#     data_layer = {
#         'session': db.session,
#         'model': Chat
#     }
#
#     @classmethod
#     def add_routes(cls, api):
#         api.route(cls, 'chat_user', '/chats/<int:id>/relationships/owner')
#         api.route(cls, 'chat_prompt', '/chats/<int:id>/relationships/prompt')
# class CSVPreview(ResourceDetail):
#     schema = PreviewSchema
#     data_layer = {
#         'session': db.session,
#         'model': CSVFile
#     }