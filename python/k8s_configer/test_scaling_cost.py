import time
import itertools
from k8s_configer import Configer
from time import strftime, localtime
import os
import utils
import math

strftime("%Y-%m-%d-%H-%M-%S", localtime())

my_configer = Configer()


def wait_deployment_replicas_until_no_unavailable(name, namespace, timeout=30):
    start_t = time.time()
    # 等待deployment所有replicas都ready,没有unavailable的
    cmd = f"kubectl -n {namespace} rollout status deployment/{name} --timeout={timeout}s"
    end_t = time.time()
    wait_t = end_t - start_t
    return wait_t


def update_deployment_replicas_until_finished(name, namespace, replicas, timeout=30) -> float:
    start_t = time.time()
    my_configer.upgrade_deployment_replicas(name=name, namespace=namespace, replicas=replicas)
    # 等待deployment的replicas达到replicas目标值
    cmd = f"kubectl -n {namespace} rollout status deployment/{name} --timeout={timeout}s"
    os.system(cmd)
    end_t = time.time()
    scaling_t = end_t - start_t
    return scaling_t



def scaling_deployment(name, namespace, init_replicas, target_replicas,) -> float:
    # 先配置成初始状态
    scaling_t = update_deployment_replicas_until_finished(name=name, namespace=namespace, replicas=init_replicas)
    # 休眠5秒
    time.sleep(5)

    # 等待deployment的replicas达到replicas目标值
    scaling_t = update_deployment_replicas_until_finished(name=name, namespace=namespace, replicas=target_replicas)
    print(f"replicas从{init_replicas}到{target_replicas},花费{scaling_t}秒!")
    return scaling_t



def exp_different_replicas_resource_node(name, namespace, init_replicas_list, target_replicas_list, resource_list, node_name_list_list, filename="scaling-cost.csv", save_root="./results", repeat=1):
    datetime_str = strftime("%Y-%m-%d-%H-%M-%S", localtime())
    filename = datetime_str + "-" + filename
    filepath = os.path.join(save_root, filename)
    
    log_dict_list = []
    for iter in range(repeat):
        print(f"第{iter}遍!")
        for node_name_list in node_name_list_list:
            my_configer.upgrade_deployment_affinity(name=name, namespace=namespace, node_name_list=node_name_list)
            for resource in resource_list:
                my_configer.update_deployment_resource(name=name, namespace=namespace, resource=resource)
                for (init_replicas, target_replicas) in itertools.product(init_replicas_list, target_replicas_list):
                    scaling_t = scaling_deployment(name=name, namespace=namespace, init_replicas=init_replicas, target_replicas=target_replicas)
                    log_dict = {
                        "name": name,
                        "namespace": namespace,
                        "node_name_list": node_name_list,
                        "node_num": len(node_name_list),
                        "init_replicas": init_replicas,
                        "target_replicas": target_replicas,
                        "delta_replicas": target_replicas - init_replicas,
                        "scaling_t": scaling_t,
                    }
                    log_dict.update(resource)
                    # 写入txt
                    with open(filepath+".txt",mode='a') as f:
                        f.write(str(log_dict)+"\n")

                    print(f"log_dict:{log_dict}")
                    log_dict_list.append(log_dict)

                    # 将pod清零
                    my_configer.upgrade_deployment_replicas(name=name, namespace=namespace, replicas=0)
                    wait_t = wait_deployment_replicas_until_no_unavailable(name=name, namespace=namespace, timeout=30)
                    # 等待 terminating
                    print(f"等待{wait_t}秒, 清零成功!")

            utils.write_dict_list_to_csv(
                filepath=filepath,
                log_dict_list=log_dict_list
            )
            print(f"保存完成至{filepath}!")


def exp_different_replicas_resource_node_with_tight_repeat(name, namespace, init_replicas_list, target_replicas_list, resource_list,
                                         node_name_list_list,
                                         filename="scaling-cost.csv", save_root="./results", repeat=1):
    datetime_str = strftime("%Y-%m-%d-%H-%M-%S", localtime())
    filename = datetime_str + "-" + filename
    filepath = os.path.join(save_root, filename)

    log_dict_list = []

    for node_name_list in node_name_list_list:
        my_configer.upgrade_deployment_affinity(name=name, namespace=namespace, node_name_list=node_name_list)
        for resource in resource_list:
            my_configer.update_deployment_resource(name=name, namespace=namespace, resource=resource)
            for (init_replicas, target_replicas) in itertools.product(init_replicas_list, target_replicas_list):
                for iter in range(repeat):
                    print(f"第{iter}遍!")
                    scaling_t = scaling_deployment(name=name, namespace=namespace, init_replicas=init_replicas,
                                                   target_replicas=target_replicas,)
                    log_dict = {
                        "name": name,
                        "namespace": namespace,
                        "node_name_list": node_name_list,
                        "node_num": len(node_name_list),
                        "init_replicas": init_replicas,
                        "target_replicas": target_replicas,
                        "delta_replicas": target_replicas - init_replicas,
                        "scaling_t": scaling_t,
                    }
                    log_dict.update(resource)
                    # 写入txt
                    with open(filepath + ".txt", mode='a') as f:
                        f.write(str(log_dict) + "\n")

                    print(f"log_dict:{log_dict}")
                    log_dict_list.append(log_dict)

                    # 将pod清零
                    my_configer.upgrade_deployment_replicas(name=name, namespace=namespace, replicas=0)
                    wait_t = wait_deployment_replicas_until_no_unavailable(name=name, namespace=namespace, timeout=30)
                    # 等待 terminating
                    if math.isnan(scaling_t):
                        time.sleep(10)
                    else:
                        time.sleep(scaling_t + 2)

                    if math.isnan(wait_t):
                        print(f"清零失败!")
                    else:
                        print(f"清零成功!")

        utils.write_dict_list_to_csv(
            filepath=filepath,
            log_dict_list=log_dict_list
        )
        print(f"保存完成至{filepath}!")


def do_exp():
    name = "nginx"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(0,17)]
    resource_list = utils.generate_resource_list(cpu_list=[0.5,1,1.5,2], memory_list=[128,256,512,1024])
    node_name_list_list = [
        ["k8s02"],
        ["k8s02", "k8s03"], 
        ["k8s02", "k8s03","k8s04"], 
        ["k8s02", "k8s03", "k8s04", "k8s05"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]
    is_wait_until_no_unavailable = False

    exp_different_replicas_resource_node(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
    )


def do_exp_2():
    name = "nginx"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(0,65)]
    resource_list = utils.generate_resource_list(cpu_list=[0.1,0.35,1,2], memory_list=[128,256,512,2048])
    node_name_list_list = [
        ["k8s02"],
        ["k8s02", "k8s03"], 
        ["k8s02", "k8s03","k8s04"], 
        ["k8s02", "k8s03", "k8s04", "k8s05"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]
    is_wait_until_no_unavailable = False

    exp_different_replicas_resource_node(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
        repeat=20
    )


def do_exp_3():
    name = "nginx"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(0,65)]
    resource_list = utils.generate_resource_list(cpu_list=[0.1,0.1,0.1,0.1], memory_list=[64,64,64,64])
    node_name_list_list = [
        ["k8s02"],
        # ["k8s02", "k8s03"], 
        # ["k8s02", "k8s03","k8s04"], 
        # ["k8s02", "k8s03", "k8s04", "k8s05"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]
    is_wait_until_no_unavailable = False

    exp_different_replicas_resource_node(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
        repeat=20
    )

def do_exp_4():
    name = "nginx"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(0,21)]
    resource_list = utils.generate_resource_list(cpu_list=[0.1], memory_list=[64])
    node_name_list_list = [
        # ["k8s02"],
        # ["k8s02", "k8s03"],
        ["k8s02", "k8s03","k8s04"], 
        # ["k8s02", "k8s03", "k8s04", "k8s05"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]
    is_wait_until_no_unavailable = False

    exp_different_replicas_resource_node(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
        repeat=16
    )

def do_exp_5():
    name = "nginx"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(1,31)]
    resource_list = utils.generate_resource_list(cpu_list=[0.1], memory_list=[64])
    node_name_list_list = [
        ["k8s02"],
        ["k8s02", "k8s03"],
        ["k8s02", "k8s03","k8s04"],
        # ["k8s02", "k8s03", "k8s04", "k8s05"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]
    is_wait_until_no_unavailable = False

    exp_different_replicas_resource_node(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
        repeat=20
    )


def do_exp_6():
    name = "nginx"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(1,31)]
    resource_list = utils.generate_resource_list(cpu_list=[0.1], memory_list=[64])
    node_name_list_list = [
        ["k8s02"],
        ["k8s02", "k8s03"],
        ["k8s02", "k8s03","k8s04"],
        # ["k8s02", "k8s03", "k8s04", "k8s05"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]
    is_wait_until_no_unavailable = False

    exp_different_replicas_resource_node(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
        repeat=20
    )


def do_exp_7():
    name = "nginx"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(1,31)]
    resource_list = utils.generate_resource_list(cpu_list=[0.1], memory_list=[64])
    node_name_list_list = [
        ["k8s02"],
        ["k8s02", "k8s03"],
        ["k8s02", "k8s03","k8s04"],
        # ["k8s02", "k8s03", "k8s04", "k8s05"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]
    is_wait_until_no_unavailable = False

    exp_different_replicas_resource_node_with_tight_repeat(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
        repeat=20
    )


def do_exp_8():
    name = "busybox"
    namespace = "default"
    init_replicas_list = [0]
    target_replicas_list = [i for i in range(1,31)]
    resource_list = utils.generate_resource_list(cpu_list=[0.1], memory_list=[64])
    node_name_list_list = [
        ["k8s02"],
        ["k8s02", "k8s03"],
        # ["k8s02", "k8s03","k8s04"],
        ["k8s02", "k8s03", "k8s04", "k8s05"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07"],
        # ["k8s02", "k8s03", "k8s04", "k8s05", "k8s06", "k8s07", "k8s08"],
    ]

    exp_different_replicas_resource_node_with_tight_repeat(
        name=name,
        namespace=namespace,
        init_replicas_list=init_replicas_list,
        target_replicas_list=target_replicas_list,
        resource_list=resource_list,
        node_name_list_list=node_name_list_list,
        repeat=3
    )



if __name__ == "__main__":
    # print(scaling_deployment(name="app", namespace="default", init_replicas=0, target_replicas=5))
    do_exp_8()
