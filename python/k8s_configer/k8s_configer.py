from kubernetes import client, config
from typing import List
import re

class Configer:
    def __init__(self, kubeconfig_path="~/.kube/config", context=None):
        try:
            config.load_kube_config(config_file=kubeconfig_path, context=context)
            print(f"成功从{kubeconfig_path}加载!")
        except Exception as e:
            print(f"获取kubeconfig文件失败")
            print(e)
            config.load_incluster_config()
            print(f"成功从incluster加载!")

        self.api = client.AppsV1Api()
        self.core = client.CoreV1Api()
        pass

    # 列举所有的namespace名称
    def get_all_namespace(self) -> List:
        ret = []
        for ns in self.core.list_namespace().items:
            ret.append(ns.metadata.name)
        return ret

    # 列举所有的service名称
    def get_all_service(self) -> List:
        result = []
        ret = self.core.list_service_for_all_namespaces(watch=False)
        for i in ret.items:
            info = {'kind': i.kind, 'namespace': i.metadata.namespace, 'name': i.metadata.name, 'ip': i.spec.cluster_ip,
                    'ports': i.spec.ports}
            result.append(info)
        return result

    def get_all_pod(self):
        result = []
        ret = self.core.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            info = {'pod_ip': i.status.pod_ip, 'namespace': i.metadata.namespace, 'name': i.metadata.name}
            result.append(info)
        return result

    def get_namespace_all_pod(self, namespace):
        result = []
        ret = self.core.list_namespaced_pod(namespace=namespace, watch=False)
        for i in ret.items:
            info = {
                'name': i.metadata.name,
                'namespace': i.metadata.namespace, 
                'phase': i.status.phase,
                'node_name': i.spec.node_name
            }
            result.append(info)
        return result

    def get_all_deployment(self):
        result = []
        ret = self.api.list_deployment_for_all_namespaces(watch=False)
        for i in ret.items:
            images = [x.image for x in i.spec.template.spec.containers]
            info = {'namespace': i.metadata.namespace, 'name': i.metadata.name, 'images': images}
            result.append(info)
        return result

    def get_namespace_deployment(self, namespace):
        result = []
        ret = self.api.list_namespaced_deployment(namespace, watch=False)
        for i in ret.items:
            images = [x.image for x in i.spec.template.spec.containers]
            info = {'namespace': i.metadata.namespace, 'name': i.metadata.name, 'images': images}
            result.append(info)
        return result

    def get_deployment_replicas(self, name="helloworld-ms", namespace="default", get_type="ready"):
        body = self.api.read_namespaced_deployment(name, namespace)
        if get_type == "ready":
            ready_replicas = body.status.ready_replicas
            if ready_replicas == None:
                ready_replicas = 0
            return ready_replicas
        elif get_type == "unavailable":
            unavailable_replicas = body.status.unavailable_replicas
            if unavailable_replicas == None:
                unavailable_replicas = 0
            return unavailable_replicas
        else:
            print(f"get_type需要为ready或者unavailable")

    def upgrade_deployment_replicas(self, name="helloworld-ms", namespace="default", replicas=2):
        # read deployment
        body = self.api.read_namespaced_deployment(name, namespace)
        # 修改 replicas
        body.spec.replicas = replicas
        try:
            self.api.patch_namespaced_deployment(name, namespace, body)
        except Exception as e:
            print("Exception when calling AppsV1Api->replace_namespaced_deployment: %s\n" % e)
            pass

    def upgrade_deployment_node_name(self, name="nginx-deployment", namespace="nginx", node_name="k8s02"):
        # read deployment
        body = self.api.read_namespaced_deployment(name, namespace)
        body.spec.template.spec.node_name = node_name
        body.spec.template.spec.affinity = None
        try:
            self.api.patch_namespaced_deployment(name, namespace, body)
        except Exception as e:
            print("Exception when calling AppsV1Api->replace_namespaced_deployment: %s\n" % e)
            pass

    def get_deployment_affinity(self, name="nginx-deployment", namespace="nginx"):
        body = self.api.read_namespaced_deployment(name, namespace)
        affinity = body.spec.template.spec.affinity
        return affinity


    def upgrade_deployment_affinity(self, name="nginx-deployment", namespace="nginx", node_name_list=None):
        # read deployment
        if node_name_list is None:
            node_name_list = ["k8s02", "k8s04"]
        body = self.api.read_namespaced_deployment(name, namespace)

        # create affinity objects
        terms = client.models.V1NodeSelectorTerm(
            match_expressions=[
                {
                    'key': 'kubernetes.io/hostname',
                    'operator': 'In',
                    'values': node_name_list
                }
            ]
        )
        node_selector = client.models.V1NodeSelector(node_selector_terms=[terms])
        node_affinity = client.models.V1NodeAffinity(
            required_during_scheduling_ignored_during_execution=node_selector
        )
        affinity = client.models.V1Affinity(node_affinity=node_affinity)

        # replace affinity in the deployment object
        body.spec.template.spec.affinity = affinity
        try:
            res = self.api.replace_namespaced_deployment(name, namespace, body)
        except Exception as e:
            print("Exception when calling AppsV1Api->replace_namespaced_deployment: %s\n" % e)
            pass

    # 获得deploymemt中affinity的字段
    def get_deployment_annotations(self, name, namespace):
        # read deployment
        body = self.api.read_namespaced_deployment(name, namespace)
        annotations = body.spec.template.metadata.annotations
        return annotations

    def get_deployment_resource(self, name, namespace, container_index=0):
        '''获得deployment中资源限制

        :param name: deployment的名称
        :param namespace: deployment所在的namespace名称
        :param
        :param container_index: 配置的是第几个容器，默认配置第一个容器
        :return: deployment的资源字典，包含以下几个key:cpu_limit,mem_limit,cpu_requests,mem_requests
        '''
        body = self.api.read_namespaced_deployment(name, namespace)
        container = body.spec.template.spec.containers[container_index]
        cpu_limit = container.resources.limits["cpu"]
        mem_limit = container.resources.limits["memory"]
        cpu_requests = container.resources.requests["cpu"]
        mem_requests = container.resources.requests["memory"]

        resource = {
            "cpu_limit":resource_unit_convert(cpu_limit),
            "mem_limit":resource_unit_convert(mem_limit),
            "cpu_requests":resource_unit_convert(cpu_requests),
            "mem_requests":resource_unit_convert(mem_requests)
        }
        return resource

    def update_deployment_resource(self, name, namespace, resource, container_index=0):
        '''更新deployment中资源限制

        :param name: deployment的名称
        :param namespace: deployment所在的namespace名称
        :param resource: deployment希望设置的资源字典，包含以下几个key:cpu_limit,mem_limit,cpu_requests,mem_requests，缺一不可
        :param container_index: 配置的是第几个容器，默认配置第一个容器
        :return: 没有返回值
        '''
        body = self.api.read_namespaced_deployment(name, namespace)
        container = body.spec.template.spec.containers[container_index]

        cpu_limit = resource["cpu_limit"]
        mem_limit = resource["mem_limit"]
        cpu_requests = resource["cpu_requests"]
        mem_requests = resource["mem_requests"]

        container.resources.limits["cpu"] = cpu_limit
        container.resources.limits["memory"] = str(mem_limit)+"Mi"
        container.resources.requests["cpu"] = cpu_requests
        container.resources.requests["memory"] = str(mem_requests)+"Mi"
        body.spec.template.spec.containers[container_index] = container

        # 更新资源限制
        try:
            self.api.replace_namespaced_deployment(name, namespace, body)
        except Exception as e:
            print("Exception when calling AppsV1Api->replace_namespaced_deployment: %s\n" % e)
            pass


# 用于处理不同资源限制单位的转换
def resource_unit_convert(str:str):
    # 利用正则表达式过滤出字母
    "[^(A-Za-z)]"
    unit = "".join(re.findall("[(A-Za-z)]", str))
    num = "".join(re.findall("[^(A-Za-z)]", str))

    # 判断单位类型，并转换
    if unit == "Mi":
        res = int(num)
    elif unit == "Gi":
        res = 1024*int(num)
    elif unit == "":
        res = int(num)
    elif unit == "m":
        res = int(num)/1000
    else:
        print(f"请检查输入的数据:{str}是否正确")
        res = None
    return res


def test_resource_update():
    my_configer = Configer(context=None)
    print(my_configer.get_all_namespace())
    print(my_configer.get_deployment_resource(name="app", namespace="default"))
    resource = {
        "cpu_limit": 2.5,
        "mem_limit": 2000,
        "cpu_requests": 0.1,
        "mem_requests": 200
    }
    my_configer.update_deployment_resource(name="app", namespace="default", resource=resource)
    print(my_configer.get_deployment_resource(name="app", namespace="default"))



def test_get_deployment_status():
    my_configer = Configer(context=None)
    print(my_configer.get_deployment_replicas(name="app", namespace="default"))
    pass


def test_update_deployment_affinity():
    my_configer = Configer(context=None)
    my_configer.upgrade_deployment_affinity(name="app", namespace="default", node_name_list=["kind-control-plane"])
    print(my_configer.get_deployment_affinity(name="app", namespace="default"))


def test_namespace_all_pod():
    my_configer = Configer(context=None)
    print(my_configer.get_namespace_all_pod(namespace="default"))


if __name__ == "__main__":
    # test_get_deployment_status()
    # test_resource_update()
    # test_update_deployment_affinity()
    test_namespace_all_pod()
    pass
