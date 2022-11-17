import csv
import itertools


def write_dict_list_to_csv(filepath, log_dict_list):
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = list(log_dict_list[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_dict_list)


def generate_resource_list(cpu_list, memory_list, shuffle=False):
    if shuffle == True:
        resource_list = []
        for (cpu, memory) in itertools.product(cpu_list, memory_list):
            resource = {
                "cpu_limit": cpu,
                "mem_limit": memory,
                "cpu_requests": cpu,
                "mem_requests": memory
            }
            resource_list.append(resource)
    elif shuffle == False:
        resource_list = []
        for (cpu, memory) in zip(cpu_list, memory_list):
            resource = {
                "cpu_limit": cpu,
                "mem_limit": memory,
                "cpu_requests": cpu,
                "mem_requests": memory
            }
            resource_list.append(resource)
    return resource_list