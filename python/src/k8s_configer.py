from kubernetes import client, config
from typing import List

api = client.AppsV1Api()
core = client.CoreV1Api()

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
        pass

    # 列举所有的namespace名称
    def list_all_namespace(self) -> List:
        ret = []
        for ns in core.list_namespace().items:
            ret.append(ns.metadata.name)
        return ret

    # 列举所有的service名称
    def list_all_service(self) -> List:
        result = []
        ret = core.list_service_for_all_namespaces(watch=False)
        for i in ret.items:
            info = {'kind': i.kind, 'namespace': i.metadata.namespace, 'name': i.metadata.name, 'ip': i.spec.cluster_ip,
                    'ports': i.spec.ports}
            result.append(info)
        return result

    def list_all_pod(self):
        result = []
        ret = core.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            info = {'pod_ip': i.status.pod_ip, 'namespace': i.metadata.namespace, 'name': i.metadata.name}
            result.append(info)
        return result

    def list_all_deployment(self):
        result = []
        ret = api.list_deployment_for_all_namespaces(watch=False)
        for i in ret.items:
            images = [x.image for x in i.spec.template.spec.containers]
            info = {'namespace': i.metadata.namespace, 'name': i.metadata.name, 'images': images}
            result.append(info)
        return result

    def list_namespace_deployment(self, namespace):
        result = []
        ret = api.list_namespaced_deployment(namespace, watch=False)
        for i in ret.items:
            images = [x.image for x in i.spec.template.spec.containers]
            info = {'namespace': i.metadata.namespace, 'name': i.metadata.name, 'images': images}
            result.append(info)
        return result

    def upgrade_deployment_replicas(self, name="helloworld-ms", namespace="default", replicas=2):
        # read deployment
        body = api.read_namespaced_deployment(name, namespace)
        # print(f"body:{body}")
        # 修改 replicas
        body.spec.replicas = replicas
        try:
            api.patch_namespaced_deployment(name, namespace, body)
            # api.replace_namespaced_deployment(name, namespace, body)
        except Exception as e:
            # print("Exception when calling AppsV1Api->replace_namespaced_deployment: %s\n" % e)
            pass

    def upgrade_deployment_node_name(self, name="nginx-deployment", namespace="nginx", node_name="k8s02"):
        # read deployment
        body = api.read_namespaced_deployment(name, namespace)
        # print(f"body:{body}")
        body.spec.template.spec.node_name = node_name
        body.spec.template.spec.affinity = None
        try:
            api.patch_namespaced_deployment(name, namespace, body)
        except Exception as e:
            # print("Exception when calling AppsV1Api->replace_namespaced_deployment: %s\n" % e)
            pass

    def upgrade_deployment_affinity(self, name="nginx-deployment", namespace="nginx", node_name_list=None):
        # read deployment
        if node_name_list is None:
            node_name_list = ["k8s02", "k8s04"]
        body = api.read_namespaced_deployment(name, namespace)
        # print(f"body:{body}")
        # print(type(body.spec.template.spec.affinity))
        # print(body.spec.template.spec.affinity)

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
            res = api.replace_namespaced_deployment(name, namespace, body)
        except Exception as e:
            # print("Exception when calling AppsV1Api->replace_namespaced_deployment: %s\n" % e)
            pass

    # 获得deploymemt中affinity的字段
    def get_deployment_annotations(self, name, namespace):
        # read deployment
        body = api.read_namespaced_deployment(name, namespace)
        annotations = body.spec.template.metadata.annotations
        return annotations


if __name__ == "__main__":
    my_configer = Configer(context="kind-kind")
    print(my_configer.list_all_namespace())





















if __name__ == "__main__":
    # res = list_all_namespace()
    # res = list_all_service()
    # res = list_all_deployment()
    # print(res)
    # upgrade_deployment_replicas(replicas=10)
    # upgrade_deployment_node_name(node_name="k8s04")
    # upgrade_deployment_affinity(name="app3", namespace="satellite", node_name_list=["k8s08","k8s06"])

    # get_deployment_annotations(name="app1", namespace="satellite")

    # print(list_namespace_deployment(namespace="satellite"))

    upgrade_deployment_affinity(name="app2", namespace="satellite", node_name_list=["edge-1","edge-0"])