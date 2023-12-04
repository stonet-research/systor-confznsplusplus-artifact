import copy
import sys

def read_file(filename):
    """ Read file and remove comments

    Args:
        filename (str): _description_

    Returns:
        list(str): A list of lines
    """
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()

    # remove all leading spaces
    ret = []
    for l in lines:
        if l[0] == '#':
            continue
        ret.append(l[:-1])

    return ret


def parse_overhead(overhead, format):
    if format == 'percent':
        return float(overhead[:-1])
    elif format == 'number':
        return int(overhead)
    else:
        assert 0, 'format {} not recognized, should be percent or number'.format(
            format)


def find_top_layer(file_contents, symbol):
    for l in file_contents:
        if l != '' and l[0] != '|':
            pass


def elicit_children(file_contents):
    """ Get children from a symbol

    Args:
        file_contents (_type_): _description_

    Returns:
        _type_: _description_
    """
    children = []

    cur_children = []
    for l in file_contents:
        if l[1:].strip() == '':
            children.append(cur_children)
            cur_children = []
        else:
            cur_children.append(l)

    if len(cur_children) != 0:
        children.append(cur_children)

    return children


def reshape_child(file_contents):
    """ Remove the blank space at line start 

    Args:
        file_contents (_type_): _description_

    Returns:
        _type_: _description_
    """
    line_has_content = 0
    for l in file_contents:
        if l.strip() == '|':
            line_has_content += 1
        else:
            break

    file_contents = file_contents[line_has_content:]

    if len(file_contents) == 0:
        return []

    processed_child = []

    num_spaces = 0
    for c in file_contents[0]:
        if c == ' ' or c == '|':
            num_spaces += 1
        else:
            break
    num_spaces -= 1
    for l in file_contents:
        processed_child.append(l[num_spaces:])

    return processed_child


def process_child(file_contents, overhead_format='number'):
    """ Parse a symbol

    Args:
        file_contents (_type_): _description_
        overhead_type (str, optional): _description_. Defaults to 'number'. percent or number

    Returns:
        _type_: _description_
    """
    #print("###")
    #print(file_contents)
    title = file_contents[0]
    file_contents = file_contents[1:]
    #print(title)

    ## TODO: if there is ---name, then there is no overhead data, process this
    # process title
    if title[0] == '|':
        title = title[1:]
    title = title.strip()

    zero_overhead = False
    if title[:3] == '---':
        zero_overhead = True

    title = title.split('-')

    title_data = []
    for l in title:
        if l != '':
            title_data.append(l)

    if zero_overhead:
        title_data = [0] + title_data

    assert len(title_data) == 2, '{}, {}'.format(len(title_data), title_data)

    overhead = 0
    if not zero_overhead:
        print(title_data)
        overhead = parse_overhead(title_data[0], overhead_format)

    name = [title_data[1]]

    # TODO: process the overhead

    addition_name = []
    children = []
    for i in range(len(file_contents)):
        l = file_contents[i]
        if l[1:].strip() == '|':
            if len(file_contents) > i + 1:
                children = file_contents[i + 1:]
            else:
                children = []
            break
        else:
            cur_addition_name = l[1:].strip()
            # If there is address in addition name, skip it
            if cur_addition_name[:2] == '0x':
                continue
            addition_name.append(cur_addition_name)

    name = name + addition_name

    # now clean up the child, child are in
    children = reshape_child(children)
    children = elicit_children(children)
    #print_children(children)

    parsed_children = []
    if len(children) != 0:
        for c in children:
            parsed_children.append(process_child(c))

    # (overhead, list name, list of children(this structure, can be an empty list))
    return [overhead, name, parsed_children]


def print_child(child):
    for c in child:
        print(c)


def print_children(children):
    for i in range(len(children)):
        print(i)
        for l in children[i]:
            print(l)
        print('')


def print_recursively(children, indent=0):
    if len(children) == 0:
        return
    # the argument is the return value of parse child
    overhead = children[0]
    names = str(children[1])

    print(' ' * indent + str(overhead))
    print(' ' * indent + str(names))
    print(' ' * indent + "|")
    for c in children[2]:
        print_recursively(c, indent + 2)
    print(' ' * indent + '|')


def is_first_level_symbol(l):
    ## TODO: This condition might change if the perf report argument changes
    if l.strip()[-1] == '-':
        return True

    return False


def process_origin_file(filename, overhead_format="number"):
    overhead_format = "number"
    parsed_data = {}
    first_level_symbols = []
    all_overhead_by_inst = 0

    f = open(filename, 'r')
    lines = f.readlines()
    f.close()

    splitted_input = []
    cur_symbol = []
    for l in lines:
        if l[0] == "#":
            pass
        elif l == '\n':
            if len(cur_symbol) != 0:
                splitted_input.append(cur_symbol)
            cur_symbol = []
        elif is_first_level_symbol(l):
            if len(cur_symbol) != 0:
                splitted_input.append(cur_symbol)
            cur_symbol = [l[:-1]]
        else:
            cur_symbol.append(l[:-1])
    if len(cur_symbol) != 0:
        splitted_input.append(cur_symbol)

    for cur_symbol in splitted_input:
        # Prase the title line
        title = cur_symbol[0]

        title = title.split(' ')
        title = [e for e in title if e != '']
        overhead_all = parse_overhead(title[0],
                                      'percent')  # Children and itself
        overhead_self_percent = parse_overhead(title[1], 'percent')
        overhead_self_samples = parse_overhead(title[2], 'number')

        all_overhead_by_inst += overhead_self_samples

        # If the over head is 0, skip it
        if overhead_all == 0:
            continue

        name = title[4]
        children = reshape_child(cur_symbol[1:])
        children = elicit_children(children)

        if len(children) == 0:
            # TODO: Write to the final result
            continue

        # in some cases, the overhead of the function itself will appear in the children
        # then there will be two same-level symbol without a father, just remove the self-overhead
        # if children[0][0] == '|':
        #     new_children = []
        #     for l in children:
        #         if l[0] == '|':
        #             new_children.append(l[1:])
        #     children = new_children

        parsed_children = []
        for c in children:
            result = process_child(c, overhead_format)
            parsed_children.append(result)

        if not name in parsed_data:
            total_instructions = 0  # + overhead_self_samples
            for c in parsed_children:
                total_instructions += c[0]
            parsed_data[name] = [total_instructions, [name], parsed_children]
            # parsed_data[name] = [overhead, [name], parsed_children]
        else:
            #assert 0, 'first level symbol {} occurs more than once'.format(
            print('first level symbol {} occurs more than once'.format(name))

    return parsed_data, all_overhead_by_inst


def get_overhead(overhead_tree, symbol):
    """
    Args:
        overhead_tree (_type_): _description_
        remove_list (str): A list of symbols to remove
    """
    if symbol in overhead_tree[1]:
        return overhead_tree[0]

    overhead = 0
    for c in overhead_tree[2]:
        overhead += get_overhead(c, symbol)

    return overhead


def remove_symbol(overhead_tree, symbol):
    """" WARNING: THIS WILL CHANGE THE ARGUMENT overhead_tree IN PLACE

    Args:
        overhead_tree (_type_): _description_
        symbol (_type_): _description_

    Returns:
        _type_: _description_
    """

    # Found the target symbol, return the value, then delete all its children, mark overhead as 0
    if symbol in overhead_tree[1]:
        overhead = overhead_tree[0]
        overhead_tree[0] = 0
        overhead_tree[2] = []

        return overhead

    overhead = 0
    for c in overhead_tree[2]:
        overhead += remove_symbol(c, symbol)

    overhead_tree[0] = overhead_tree[0] - overhead

    return overhead


# --call-graph=<graph,0,caller,function,count>
def parse_report_file(filename):
    # classification dict[class] -> symbol that belong to the class
    classification = {
        'app': [
            'fio_ioring_commit', '__fio_gettime', 'account_io_completion',
            'add_clat_sample', 'add_lat_sample', 'fio_ioring_prep',
            'fio_ioring_queue', 'get_next_rand_block', 'io_queue_event',
            'io_u_mark_complete', 'io_u_mark_depth', 'lock_file', 'log_io_u',
            'ntime_since', 'td_io_commit', 'td_io_getevents', 'td_io_prep',
            'td_io_queue', 'utime_since_now', 'get_io_u', 'io_u_mark_submit',
            'fio_ioring_getevents', 'fio_ioring_event', 'fio_libaio_getevents',
            'io_u_queued_complete', 'fio_libaio_event', 'io_completed',
            'ramp_time_over', 'run_threads', 'put_file'
        ],
        'interface': [
            'io_submit_sqes',
            'blkdev_read_iter',
            'rw_verify_area',
            'io_do_iopoll',
            # aio
            #'asm_common_interrupt',
            'io_submit_one',
            'io_getevents',
            'do_io_getevents'
        ],
        'block': [
            'bio_alloc_kiocb', 'bio_associate_blkg', 'bio_iov_iter_get_pages',
            'bio_set_pages_dirty', 'blk_finish_plug', 'submit_bio',
            'blk_mq_end_request', 'blkdev_direct_IO', 'ret_from_fork'
        ],
        'driver': ['nvme_queue_rq', 'nvme_irq'],
        'sys': [
            'asm_common_interrupt',
            'entry_SYSCALL_64',
            'syscall_return_via_sysret',
            'syscall',
        ]
    }

    # symbols: a list of symbols to record, for each symbol
    # (symbol_name, [list of symbols to excluded if they occurs in the call tree of the symbol])
    symbol = [
        # fio
        ('fio_ioring_commit', [
            'entry_SYSCALL_64', 'syscall_return_via_sysret',
            'asm_common_interrupt'
        ]),
        ('__fio_gettime', ['asm_common_interrupt']),
        ('account_io_completion', ['asm_common_interrupt']),
        ('add_clat_sample', ['asm_common_interrupt']),
        ('add_lat_sample', ['asm_common_interrupt']),
        ('fio_ioring_prep', ['asm_common_interrupt']),
        ('fio_ioring_queue', ['asm_common_interrupt']),
        ('get_next_rand_block', ['asm_common_interrupt']),
        ('io_queue_event', ['asm_common_interrupt']),
        ('io_u_mark_complete', ['asm_common_interrupt']),
        ('io_u_mark_depth', ['asm_common_interrupt']),
        ('lock_file', ['asm_common_interrupt']),
        ('log_io_u', ['asm_common_interrupt']),
        ('ntime_since', ['asm_common_interrupt']),
        ('put_file', ['asm_common_interrupt']),
        ('td_io_commit', ['asm_common_interrupt']),
        ('td_io_getevents', ['asm_common_interrupt']),
        ('td_io_prep', ['asm_common_interrupt']),
        ('td_io_queue', ['asm_common_interrupt']),
        ('utime_since_now', ['asm_common_interrupt']),
        ('get_io_u', ['asm_common_interrupt']),
        ('io_u_mark_submit', ['asm_common_interrupt']),
        ('fio_ioring_getevents', ['asm_common_interrupt', 'entry_SYSCALL_64']),
        ('fio_ioring_event', ['asm_common_interrupt']),
        ('fio_libaio_getevents', ['asm_common_interrupt']),
        ('fio_libaio_event', ['asm_common_interrupt']),
        ('io_u_queued_complete', ['asm_common_interrupt']),
        ('io_completed', ['asm_common_interrupt']),
        ('ramp_time_over', ['asm_common_interrupt']),
        ('run_threads', [
            'asm_common_interrupt', 'get_io_u', 'io_queue_event',
            'io_u_queued_complete', 'td_io_queue', '__fio_gettime',
            '__get_io_u', 'fio_gettime', 'get_file', 'get_next_rand_block',
            'utime_since_now', 'fio_ioring_commit '
        ]),
        # iouring
        ('io_submit_sqes', [
            'blkdev_read_iter', 'rw_verify_area', 'asm_common_interrupt',
            'blk_finish_plug'
        ]),
        ('io_do_iopoll', [
            'asm_common_interrupt',
        ]),
        ('ret_from_fork', ['asm_common_interrupt', 'io_submit_sqes']),
        # aio
        ('do_io_getevents', ['asm_common_interrupt']),
        ('io_submit_one', ['blkdev_read_iter']),
        # fs
        ('blkdev_read_iter', ['blkdev_direct_IO', 'asm_common_interrupt']),
        ('rw_verify_area', ['asm_common_interrupt']),
        ('io_getevents', ['asm_common_interrupt']),
        ('blkdev_direct_IO', [
            'bio_alloc_kiocb', 'bio_associate_blkg', 'bio_iov_iter_get_pages',
            'bio_set_pages_dirty', 'blk_finish_plug', 'submit_bio',
            'asm_common_interrupt'
        ]),

        # blk layer
        ('bio_alloc_kiocb', ['asm_common_interrupt']),
        ('bio_associate_blkg', ['asm_common_interrupt']),
        ('bio_iov_iter_get_pages', ['asm_common_interrupt']),
        ('bio_set_pages_dirty', ['asm_common_interrupt']),
        ('blk_finish_plug', ['nvme_queue_rq', 'asm_common_interrupt']),
        ('submit_bio', ['asm_common_interrupt']),
        ('blk_mq_end_request', ['asm_common_interrupt']),
        ('nvme_queue_rq', ['asm_common_interrupt']),
        ('nvme_irq', ['blk_mq_end_request']),
        #("NO FOUND", []),
        # system
        ('asm_common_interrupt', [
            'nvme_irq', 'bio_iov_iter_get_pages', 'blk_finish_plug',
            'blk_update_request', 'blk_mq_free_request'
        ]),
        ('entry_SYSCALL_64', [
            'io_submit_sqes', 'asm_common_interrupt', 'blkdev_iopoll',
            'io_do_iopoll', 'do_io_getevents', 'io_submit_one', 'vfs_read'
        ]),
        ('syscall_return_via_sysret', ['asm_common_interrupt']),
        ('syscall', ['entry_SYSCALL_64', 'asm_common_interrupt'])
        # ('bio_alloc_kiocb', ['asm_common_interrupt']),
        # ('bio_alloc_kiocb', ['asm_common_interrupt'])

        # IO schedulers
    ]

    ## check corresponding
    symbols_in_classify = set()
    for v in classification.values():
        for s in v:
            if not s in symbols_in_classify:
                symbols_in_classify.add(s)
            else:
                raise Exception(
                    "symbol {} occurs more than one in classification".format(
                        s))

    for i in symbol:
        s = i[0]
        if not s in symbols_in_classify:
            raise Exception("symbol {} not occurs in classification".format(s))

    parsed_data, all_overhead_by_inst = process_origin_file(filename)

    statics = 0
    all_overheads = {}

    for item in symbol:
        name = item[0]
        print(name)
        excluded_symbol = item[1]
        if not name in parsed_data:
            print(name, "NOT FOUND")
            continue
        children = copy.deepcopy(parsed_data[name])

        # Overhead not belongs to the symbol
        overheads = 0
        for s in excluded_symbol:
            overheads += get_overhead(children, s)
            remove_symbol(children, s)
        # TODO: change this symbol item[0] -> name
        print(name, parsed_data[name][0], overheads,
              parsed_data[name][0] - overheads)
        all_overheads[item[0]] = parsed_data[name][0] - overheads
        statics += parsed_data[name][0] - overheads

    print('')

    print("Selected symbols:")
    selected_symbols = [
        'entry_SYSCALL_64', 'asm_common_interrupt', 'io_do_iopoll'
    ]
    for ss in selected_symbols:
        ss_overheads = 0
        if ss in all_overheads:
            ss_overheads = all_overheads[ss]

        print(ss, ":", ss_overheads)

    print("Classified:", statics, '/', all_overhead_by_inst,
          statics / all_overhead_by_inst)

    ret_key = ['app', 'interface', 'block', 'driver', 'sys']
    ret = []

    print("Overheads by layer:\n")
    for layer in ret_key:
        symbols = classification[layer]
        cur_layer_overhead = 0
        for s in symbols:
            if s in all_overheads:
                cur_layer_overhead += all_overheads[s]
        print(layer, ':', cur_layer_overhead,
              cur_layer_overhead / all_overhead_by_inst)
        ret.append(cur_layer_overhead / all_overhead_by_inst)

    return ret


def get_scheduler_overhead(filename):
    # classification dict[class] -> symbol that belong to the class
    classification = {
        'bfq': [
            'bfq_insert_requests',
            'bfq_dispatch_request',
            'bfq_bio_merge',
            'bfq_completed_request',
            'bfq_has_work',
            'bfq_limit_depth',
            'bfq_prepare_request',
        ],
        'mq-deadline': [
            'dd_insert_requests',
            'dd_dispatch_request',
            'dd_bio_merge',
            'dd_completed_request',
            'dd_has_work',
            'dd_limit_depth',
            'dd_prepare_request',
        ],
        'kyber': [
            'kyber_insert_requests',
            'kyber_dispatch_request',
            'kyber_bio_merge',
            'kyber_completed_request',
            'kyber_has_work',
            'kyber_limit_depth',
            'kyber_prepare_request',
        ],
    }

    # symbols: a list of symbols to record, for each symbol
    # (symbol_name, [list of symbols to excluded if they occurs in the call tree of the symbol])
    symbol = [
        # kyber

        # bfq
        ('bfq_insert_requests', ['asm_common_interrupt']),
        ('bfq_dispatch_request', ['asm_common_interrupt']),
        ('bfq_bio_merge', ['asm_common_interrupt']),
        ('bfq_completed_request', ['asm_common_interrupt']),
        ('bfq_has_work', ['asm_common_interrupt']),
        ('bfq_limit_depth', ['asm_common_interrupt']),
        ('bfq_prepare_request', ['asm_common_interrupt']),
        # kyber
        ('kyber_insert_requests', ['asm_common_interrupt']),
        ('kyber_dispatch_request', ['asm_common_interrupt']),
        ('kyber_completed_request', ['asm_common_interrupt']),
        ('kyber_limit_depth', ['asm_common_interrupt']),
        ('kyber_bio_merge', ['asm_common_interrupt']),
        ('kyber_has_work', ['asm_common_interrupt']),
        ('kyber_prepare_request', ['asm_common_interrupt']),
        # mq-deadline
        ('dd_insert_requests', ['asm_common_interrupt']),
        ('dd_dispatch_request', ['asm_common_interrupt']),
        ('dd_completed_request', ['asm_common_interrupt']),
        ('dd_limit_depth', ['asm_common_interrupt']),
        ('dd_bio_merge', ['asm_common_interrupt']),
        ('dd_has_work', ['asm_common_interrupt']),
        ('dd_prepare_request', ['asm_common_interrupt']),
    ]

    ## check corresponding
    # symbols_in_classify = set()
    # for v in classification.values():
    #     for s in v:
    #         if not s in symbols_in_classify:
    #             symbols_in_classify.add(s)
    #         else:
    #             raise Exception(
    #                 "symbol {} occurs more than one in classification".format(
    #                     s))

    # for i in symbol:
    #     s = i[0]
    #     if not s in symbols_in_classify:
    #         raise Exception("symbol {} not occurs in classification".format(s))

    parsed_data, all_overhead_by_inst = process_origin_file(filename)

    statics = 0
    all_overheads = {}

    for item in symbol:
        name = item[0]
        print(name)
        excluded_symbol = item[1]
        if not name in parsed_data:
            print(name, "NOT FOUND")
            continue
        children = copy.deepcopy(parsed_data[name])

        # Overhead not belongs to the symbol
        overheads = 0
        for s in excluded_symbol:
            overheads += get_overhead(children, s)
            remove_symbol(children, s)
        # TODO: change this symbol item[0] -> name
        print(name, parsed_data[name][0], overheads,
              parsed_data[name][0] - overheads)
        all_overheads[item[0]] = parsed_data[name][0] - overheads
        statics += parsed_data[name][0] - overheads

    print('')

    print("Selected symbols:")
    selected_symbols = []
    for i in symbol:
        selected_symbols.append(i[0])
    for ss in selected_symbols:
        ss_overheads = 0
        if ss in all_overheads:
            ss_overheads = all_overheads[ss]

        print(ss, ":", ss_overheads)

    print("Classified:", statics, '/', all_overhead_by_inst,
          statics / all_overhead_by_inst)

    ret_key = ['bfq', 'kyber', 'mq-deadline']
    ret = {}

    print("Overheads by layer:\n")
    for layer in ret_key:
        symbols = classification[layer]
        cur_layer_overhead = 0
        for s in symbols:
            if s in all_overheads:
                cur_layer_overhead += all_overheads[s]
        print(layer, ':', cur_layer_overhead,
              cur_layer_overhead / all_overhead_by_inst)
        ret[layer] = (cur_layer_overhead / all_overhead_by_inst)

    return ret


if __name__ == '__main__':
    filename = sys.argv[1]
    ret = get_scheduler_overhead(filename)
    # ret = parse_report_file(filename)
    print(ret)