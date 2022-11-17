import time
import itertools
from k8s_configer import Configer
from time import strftime, localtime
import os
import utils


strftime("%Y-%m-%d-%H-%M-%S", localtime())

my_configer = Configer()

def update_deployment_replicas_until_finished(name, namespace, replicas, timeout=30) -> float:
    my_configer.upgrade_deployment_replicas(name=name, namespace=namespace, replicas=replicas)
    # 等待
    start_t = time.time()
    while True:
        current_available_replicas = my_configer.get_deployment_replicas(name=name, namespace=namespace)
        print(f"当前replicas:{current_available_replicas}")
        if current_available_replicas == replicas:
            break
        if time.time() - start_t > timeout:
            return float("NaN")
        time.sleep(0.1)
    end_t = time.time()
    scaling_t = end_t - start_t
    return scaling_t


def scaling_deployment(name, namespace, init_replicas, target_replicas) -> float:
    # 先配置成初始状态
    update_deployment_replicas_until_finished(name=name, namespace=namespace, replicas=init_replicas)
    # 开始scaling
    print(f"开始计时")
    start_t = time.time()
    update_deployment_replicas_until_finished(name=name, namespace=namespace, replicas=target_replicas)
    print(f"结束计时")
    end_t = time.time()
    scaling_t = end_t - start_t
    return scaling_t



def exp_different_replicas_resource_node(name, namespace, init_replicas_list, target_replicas_list, resource_list, node_name_list_list, filename="scaling-cost.csv", save_root="./results"):
    log_dict_list = []
    for node_name_list in node_name_list_list:
        my_configer.upgrade_deployment_affinity(name=name, namespace=namespace, node_name_list=node_name_list)
        for resource in resource_list:
            my_configer.update_deployment_resource(name=name, namespace=namespace, resource=resource)
            for (init_replicas, target_replicas) in itertools.product(init_replicas_list, target_replicas_list):
                scaling_t = scaling_deployment(name=name, namespace=namespace, init_replicas=init_replicas, target_replicas=target_replicas)
                log_dict = {
                    "node_name_list": node_name_list,
                    "init_replicas": init_replicas,
                    "target_replicas": target_replicas,
                    "scaling_t": scaling_t,
                }
                log_dict.update(resource)
                print(f"log_dict:{log_dict}")
                log_dict_list.append(log_dict)
        datetime_str = strftime("%Y-%m-%d-%H-%M-%S", localtime())
        filename = datetime_str + "-" + filename
        filepath = os.path.join(save_root, filename)
        utils.write_dict_list_to_csv(
            filepath=filepath,
            log_dict_list=log_dict_list
        )
        print(f"保存完成至{filepath}!")


def do_exp():
    name = "app"
    namespace = "default"
    init_replicas_list = [0,1,2,3,4,5]
    target_replicas_list = [0,1,2,3,4,5]
    resource_list = utils.generate_resource_list(cpu_list=[0.1,0.2], memory_list=[128,192])
    node_name_list_list = [["kind-control-plane"]]

    exp_different_replicas_resource_node(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list
    )





if __name__ == "__main__":
    # print(scaling_deployment(name="app", namespace="default", init_replicas=0, target_replicas=5))
    do_exp()
