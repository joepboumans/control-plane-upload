#!/usr/bin/python3
import logging

from ptf import config
import ptf.testutils as testutils
from bfruntime_client_base_tests import BfRuntimeTest
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import random
import time

swports = []
print(config)
for device, port, ifname in config["interfaces"]:
    swports.append(port)
    swports.sort()

if swports == []:
    swports = list(range(9))


# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('control_plane_upload')
if not len(logger.handlers):
    sh = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s - %(name)s - %(funcName)s]: %(message)s')
    sh.setFormatter(formatter)
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
        logger.info("Starting test")
        bfrt_info = self.bfrt_info
        target = self.target
        forward_table = self.forward_table
        key_list = []

        logger.info("Populating foward table...")
        # Populate key and data
        num_entries =  10
        dip = ['%d.%d.%d.%d' % (random.randint(0,255), random.randint(0,255),
                                random.randint(0,255), random.randint(0,255)) for x in range(num_entries)]
        for i in range(num_entries):
            key_list.append(forward_table.make_key([gc.KeyTuple('hdr.ipv4.dst_addr', dip[i])]))
        data_list = [forward_table.make_data([], 'SwitchIngress.hit')]

        logger.info("...done")
