#!/usr/bin/python3
import logging
from collections import namedtuple

from ptf import config
import ptf.testutils as testutils
from p4testutils.misc_utils import *
from bfruntime_client_base_tests import BfRuntimeTest
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import random
import time

swports = get_sw_ports()
logger = logging.getLogger('control_plane_upload')

if not len(logger.handlers):
    sh = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s - %(name)s - %(funcName)s]: %(message)s')
    sh.setFormatter(formatter)
    sh.setLevel(logging.DEBUG)
    logger.addHandler(sh)

class TestTest(BfRuntimeTest):
    def setUp(self):
        logger.info("Starting setup")
        client_id = 0
        BfRuntimeTest.setUp(self, client_id)
        logger.info("\tfinished BfRuntimeSetup")

        self.bfrt_info = self.interface.bfrt_info_get("control_plane_upload")
        self.forward_table = self.bfrt_info.table_get("SwitchIngress.forward")
        self.forward_table.info.key_field_annotation_add("hdr.ipv4.dst_addr", "ipv4")
        self.target = gc.Target(device_id=0, pipe_id=0xffff)
        logger.info("Finished setup")

    def runTest(self):
        logger.info("Start testing")
        ig_port = swports[1]
        seed=1001
        bfrt_info = self.bfrt_info
        target = self.target
        forward_table = self.forward_table

        key_tuple = namedtuple('key', 'dst_ip')
        data_tuple = namedtuple('data', 'eg_port')
        key_list = []
        data_list = []
        forward_dict = {}

        ''' TC:1 Setting and validating forwarding plane via get'''
        logger.info("Populating foward table...")
        num_entries =  10
        logger.info(f"Generating {num_entries} random ips with seed {seed}")
        ip_list = self.generate_random_ip_list(num_entries, seed)
        logger.info("Adding entries to forward table")
        for ip_entry in ip_list:
            dst_addr = getattr(ip_entry, "ip")
            eg_port = swports[random.randint(0, len(swports) - 1)]

            key_list.append(key_tuple(dst_addr))
            data_list.append(data_tuple(eg_port))

            logger.debug(f"\tinserting table entry with IP {dst_addr} and egress port {eg_port}")
            key = forward_table.make_key([gc.KeyTuple('hdr.ipv4.dst_addr', dst_addr)])
            data = forward_table.make_data([gc.DataTuple('port', eg_port)], 'SwitchIngress.hit')

            forward_table.entry_add(target, [key], [data])
            
            key.apply_mask()
            forward_dict[key] = data


        logger.info("Validate forwarding table via get")
        resp = forward_table.entry_get(target)
        for data, key in resp:
            assert forward_dict[key] == data
            forward_dict.pop(key)
        assert len(forward_dict) == 0
        logger.info("Forward plane validated")

        ''' TC:2 Validate forward plane via packets'''




                



    def tearDown(self):
        # delete all entries
        self.forward_table.entry_del(self.target)
        usage = next(self.forward_table.usage_get(self.target, []))
        assert usage == 0
        BfRuntimeTest.tearDown(self)
