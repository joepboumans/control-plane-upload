from ipaddress import ip_address



def get_pg_info(dev_port, queue_id):
    pipe_num = dev_port >> 7
    entry = bfrt.tf1.tm.port.cfg.get(dev_port, print_ents=False)
    pg_id = entry.data[b'pg_id']
    pg_queue = entry.data[b'egress_qid_queues'][queue_id]

    print('DEV_PORT: {} QueueID: {} --> Pipe: {}, PG_ID: {}, PG_QUEUE: {}'.format(dev_port, queue_id, pipe_num, pg_id, pg_queue))

    return pipe_num, pg_id, pg_queue


# Clear All tables
def clear_all():
    global p4
 
    The order is important. We do want to clear from the top, i.e.
    delete objects that use other objects, e.g. table entries use
    selector groups and selector groups use action profile members
 
    # Clear Match Tables
    for table in p4.info(return_info=True, print_info=False):
        if table['type'] in ['MATCH_DIRECT', 'MATCH_INDIRECT_SELECTOR']:
            print("Clearing table {}".format(table['full_name']))
            for entry in table['node'].get(regex=True):
                entry.remove()
    # Clear Selectors
    for table in p4.info(return_info=True, print_info=False):
        if table['type'] in ['SELECTOR']:
            print("Clearing ActionSelector {}".format(table['full_name']))
            for entry in table['node'].get(regex=True):
                entry.remove()
    # Clear Action Profiles
    for table in p4.info(return_info=True, print_info=False):
        if table['type'] in ['ACTION_PROFILE']:
            print("Clearing ActionProfile {}".format(table['full_name']))
            for entry in table['node'].get(regex=True):
                entry.remove()
 
    # Clearing register
    for table in p4.info(return_info=True, print_info=False):
        if table['type'] in ['REGISTER']:
            print("Clearing Regitser {}".format(table['full_name']))
            table['node'].clear()



def main():
    p4 = bfrt.control_plane_upload.pipe

    clear_all()

    forward = p4.SwitchIngress.forward

    forward.add_with_hit(dst_addr="10.0.0.2",  port=5)
    forward.add_with_hit(dst_addr="10.0.0.1",  port=3)

    myPorts=[3,5]
    bfrt.tf1.tm.port.sched_cfg.mod(dev_port=3, max_rate_enable=True)
    bfrt.tf1.tm.port.sched_cfg.mod(dev_port=5, max_rate_enable=True)
    # bfrt.tf1.tm.port.sched_cfg.mod(dev_port=3, min_rate_enable=True)
    # # bfrt.tf1.tm.port.sched_cfg.mod(dev_port=5, min_rate_enable=True)
    bfrt.tf1.tm.port.sched_shaping.mod(dev_port=3, unit='PPS', provisioning='MIN_ERROR', max_rate=1, max_burst_size=1)
    bfrt.tf1.tm.port.sched_shaping.mod(dev_port=5, unit='PPS', provisioning='MIN_ERROR', max_rate=1, max_burst_size=1)

    for port_number in myPorts:
        for queue_id in range(8):
            pipe_num, pg_id, pg_queue=get_pg_info(port_number, queue_id)
            bfrt.tf1.tm.queue.sched_cfg.mod(pipe=pipe_num, pg_id=pg_id, pg_queue=pg_queue, min_priority=queue_id,max_priority=queue_id)
#

    bfrt.complete_operations()

if __name__ == "__main__":
    main()

