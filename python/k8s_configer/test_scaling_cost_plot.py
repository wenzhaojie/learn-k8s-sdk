from matplotlib import pyplot as plt
import pandas as pd
from plot import Plotter


def data_filter(df, node_num=None, cpu=None, memory=None, delta_replicas=None):
    filtered_df = df.dropna()
    if node_num != None:
        filtered_df = filtered_df.loc[df["node_num"]==node_num]
    if cpu != None:
        filtered_df = filtered_df.loc[df["cpu_limit"]==cpu]
    if memory != None:
        filtered_df = filtered_df.loc[df["mem_limit"]==memory]
    if delta_replicas != None:
        filtered_df = filtered_df.loc[df["delta_replicas"]==delta_replicas]

    return filtered_df


def plot_different_cpu(df, node_num=1, cpu_list=None):
    # 每一个 cpu 对应一个图例
    x_list = [] # delta_replicas
    y_list = [] # scaling_t
    y_label_list = [] # cpu

    for cpu in cpu_list:
        data = data_filter(df, node_num=node_num, cpu=cpu)
        x = data["delta_replicas"]
        y = data["scaling_t"]
        x_list.append(x)
        y_list.append(y)
        y_label_list.append(str(cpu))

    # meta data
    title = f"node_num-{node_num}"


    my_plotter = Plotter()
    my_plotter.plot_lines(
        x_list=x_list,
        y_list=y_list,
        y_label_list=y_label_list,
        x_label="delta_replicas",
        y_label="scaling_t",
        title=title,
        save_root="./results/plot",
        filename=f"{title}.png",
        legend_title="cpu"
    )


def plot_different_node_num(df, cpu=0.5, node_num_list=None):
    # 每一个 node_num 对应一个图例
    x_list = [] # delta_replicas
    y_list = [] # scaling_t
    y_label_list = [] # node_num

    for node_num in node_num_list:
        data = data_filter(df, node_num=node_num, cpu=cpu)
        x = data["delta_replicas"].values.tolist()
        y = data["scaling_t"].values.tolist()
        x_list.append(x)
        y_list.append(y)
        y_label_list.append(str(node_num))

    print(f"len(x_list):{len(x_list)}")
    print(f"len(y_list):{len(y_list)}")
    print(f"y_label_list:{y_label_list}")

    # meta data
    title = f"cpu-{cpu}"

    my_plotter = Plotter(figsize=(20,10))
    my_plotter.plot_lines(
        x_list=x_list,
        y_list=y_list,
        y_label_list=y_label_list,
        x_label="delta_replicas",
        y_label="scaling_t",
        title=title,
        save_root="./results/plot",
        filename=f"{title}.png",
        legend_title="node_num"
    )



def test_data_filter(node_num=1):
    # 加载csv文件
    df = pd.read_csv(f"./results/res.csv")
    res = data_filter(df=df, node_num=1, cpu=None, memory=None, delta_replicas=None)
    print(res)
    pass


def test_plot_different_cpu(node_num=1):
    # 加载csv文件
    df = pd.read_csv(f"./results/res.csv")
    plot_different_cpu(
        df,
        node_num=node_num,
        cpu_list=[0.5,1,1.5,2]
    )

def test_plot_different_node_num(cpu=0.5):
    # 加载csv文件
    df = pd.read_csv(f"./results/res.csv")
    plot_different_node_num(
        df,
        cpu=cpu,
        node_num_list=[1,2,3,4,5,6,7]
    )


if __name__ == "__main__":
    # test_data_filter()
    for cpu in [0.5,1,1.5,2]:
        test_plot_different_node_num(cpu=cpu)
    for node_num in [1,2,3,4,5,6,7]:
        test_plot_different_cpu(node_num=node_num)