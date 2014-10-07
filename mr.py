# -*- coding: utf-8 -*-

import os

from mapreduce import base_handler, mapreduce_pipeline

from google.appengine.api import app_identity
from models import MapReduceResult


def predator_count_map(animal):
    aid = animal.key.id()
    pids = [p.id() for p in animal.prey]
    for pid in pids:
        yield (pid, aid)


def predator_count_reduce(animal_id, predator_ids):
    yield "%s,%i\n" % (animal_id, len(predator_ids))


class StoreOutput(base_handler.PipelineBase):
    def run(self, pipeline_id, output):
        mrr = MapReduceResult.get_by_id(pipeline_id)
        mrr.result_file = output[0]
        mrr.put()


class PredatorCountPipeline(base_handler.PipelineBase):

    def run(self):
        BUCKET_NAME = os.environ.get('BUCKET_NAME',
                                     app_identity.get_default_gcs_bucket_name())
        
        output = yield mapreduce_pipeline.MapreducePipeline(
            "word_count",
            "mr.predator_count_map",
            "mr.predator_count_reduce",
            "mapreduce.input_readers.DatastoreInputReader",
            "mapreduce.output_writers.FileOutputWriter",
            mapper_params={
                "input_reader": {
                    "entity_kind": "models.Animal"
                },
            },
            reducer_params={
                "output_writer": {
                    "filesystem": "gs",
                    "gs_bucket_name": BUCKET_NAME,
                    "mime_type": "text/plain"
                },
            })
        
        yield StoreOutput(self.pipeline_id, output)
