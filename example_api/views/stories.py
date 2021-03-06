import logging
from random import random

from nefertari.elasticsearch import ES
from nefertari.json_httpexceptions import (
    JHTTPCreated, JHTTPOk)

from example_api.views.base import BaseView
from example_api.model import Story

log = logging.getLogger(__name__)


class ArbitraryObject(object):
    def __init__(self, *args, **kwargs):
        self.attr = random()

    def to_dict(self, *args, **kwargs):
        return dict(attr=self.attr)


class StoriesView(BaseView):
    _model_class = Story

    def get_collection_es(self):
        search_params = []

        if 'q' in self._query_params:
            search_params.append(self._query_params.pop('q'))

        self._raw_terms = ' AND '.join(search_params)

        return ES('Story').get_collection(
            _raw_terms=self._raw_terms,
            **self._query_params)

    def index(self):
        return self.get_collection_es()

    def show(self, **kwargs):
        return self.context

    def create(self):
        story = Story(**self._json_params)
        story.arbitrary_object = ArbitraryObject()
        story.save()
        pk_field = Story.pk_field()
        return JHTTPCreated(
            location=self.request._route_url(
                'stories', getattr(story, pk_field)),
            resource=story.to_dict(),
            request=self.request,
        )

    def update(self, **kwargs):
        pk_field = Story.pk_field()
        kwargs = self.resolve_kwargs(kwargs)
        story = Story.get_resource(**kwargs).update(self._json_params)
        return JHTTPOk(location=self.request._route_url(
            'stories', getattr(story, pk_field)))

    def delete(self, **kwargs):
        kwargs = self.resolve_kwargs(kwargs)
        Story._delete(**kwargs)
        return JHTTPOk()

    def delete_many(self):
        es_stories = self.get_collection_es()
        stories = Story.filter_objects(
            es_stories, _limit=self._query_params['_limit'])
        count = Story.count(stories)

        if self.needs_confirmation():
            return stories

        Story._delete_many(stories)

        return JHTTPOk("Delete %s %s(s) objects" % (
            count, self._model_class.__name__))

    def update_many(self):
        es_stories = self.get_collection_es()
        stories = Story.filter_objects(
            es_stories, _limit=self._query_params['_limit'])
        count = Story.count(stories)
        Story._update_many(stories, **self._json_params)

        return JHTTPOk("Updated %s %s(s) objects" % (
            count, self._model_class.__name__))
