#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: common.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>

import tensorflow as tf
import os
import re

from .base import Callback, PeriodicCallback
from ..utils import *

__all__ = ['PeriodicSaver', 'SummaryWriter']

class PeriodicSaver(PeriodicCallback):
    def __init__(self, period=1, keep_recent=10, keep_freq=0.5):
        super(PeriodicSaver, self).__init__(period)
        self.path = os.path.join(logger.LOG_DIR, 'model')
        self.keep_recent = keep_recent
        self.keep_freq = keep_freq

    def _before_train(self):
        self.saver = tf.train.Saver(
            max_to_keep=self.keep_recent,
            keep_checkpoint_every_n_hours=self.keep_freq)

    def _trigger(self):
        self.saver.save(
            tf.get_default_session(),
            self.path,
            global_step=self.global_step)

class SummaryWriter(Callback):
    def __init__(self, print_tag=None):
        self.log_dir = logger.LOG_DIR
        self.print_tag = print_tag if print_tag else ['train_cost']

    def _before_train(self):
        self.writer = tf.train.SummaryWriter(
            self.log_dir, graph_def=self.sess.graph_def)
        tf.add_to_collection(SUMMARY_WRITER_COLLECTION_KEY, self.writer)
        self.summary_op = tf.merge_all_summaries()

    def trigger_epoch(self):
        # check if there is any summary
        if self.summary_op is None:
            return
        summary_str = self.summary_op.eval()
        summary = tf.Summary.FromString(summary_str)
        for val in summary.value:
            #print val.tag
            val.tag = re.sub('tower[0-9]*/', '', val.tag)
            if val.tag in self.print_tag:
                assert val.WhichOneof('value') == 'simple_value', \
                    'Cannot print summary {}: not a simple_value summary!'.format(val.tag)
                logger.info('{}: {:.4f}'.format(val.tag, val.simple_value))
        self.writer.add_summary(summary, get_global_step())

    def _after_train(self):
        self.writer.close()

