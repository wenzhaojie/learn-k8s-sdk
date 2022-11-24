from matplotlib import pyplot as plt
import pandas as pd
from plot import Plotter
import os


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


def plot_different_cpu(df, delta_replicas_list=[i for i in range(1,21)], node_num=1, cpu_list=None, exp_name=None):
    # 每一个 cpu 对应一个图例
    x_list = [] # delta_replicas
    y_list = [] # scaling_t
    y_label_list = [] # cpu
    for cpu in cpu_list:
        x = []
        y = []
        for delta_replicas in delta_replicas_list:
        
            data = data_filter(df, node_num=node_num, cpu=cpu, delta_replicas=delta_replicas)
            xx = data["delta_replicas"].mean()
            yy = data["scaling_t"].mean()
            x.append(xx)
            y.append(yy)

        x_list.append(x)
        y_list.append(y)
        y_label_list.append(str(cpu))

    # meta data
    title = f"node_num-{node_num}"
    save_root = os.path.join("./results", exp_name)
    os.makedirs(save_root, exist_ok=True)


    my_plotter = Plotter()
    my_plotter.plot_lines(
        x_list=x_list,
        y_list=y_list,
        y_label_list=y_label_list,
        x_label="delta_replicas",
        y_label="scaling_t",
        title=title,
        save_root=save_root,
        filename=f"{title}.png",
        legend_title="cpu"
    )


def plot_different_node_num(df, cpu=0.5, node_num_list=None, exp_name=None):
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
    save_root = os.path.join("./results", exp_name)
    os.makedirs(save_root, exist_ok=True)

    my_plotter = Plotter(figsize=(20,10))
    my_plotter.plot_lines(
        x_list=x_list,
        y_list=y_list,
        y_label_list=y_label_list,
        x_label="delta_replicas",
        y_label="scaling_t",
        title=title,
        save_root=save_root,
        filename=f"{title}.png",
        legend_title="node_num"
    )


def plot_box_with_different_node_num(df, cpu, node_num_list, delta_replicas_list=None, exp_name=None):
    # 每一个 node_num 对应一个图例
    x_list = [] # delta_replicas
    y_list = [] # scaling_t
    box_label_list = [] # node_num

    for node_num in node_num_list:
        x = []
        y = []
        for delta_replicas in delta_replicas_list:
            data = data_filter(df, node_num=node_num, cpu=cpu, delta_replicas=delta_replicas)
            xx = data["delta_replicas"].mean()
            yy = data["scaling_t"]
            x.append(xx)
            y.append(yy)

        x_list.append(x)
        y_list.append(y)
        box_label_list.append(str(node_num))

    print(f"len(x_list):{len(x_list)}")
    print(f"len(y_list):{len(y_list)}")
    print(f"box_label_list:{box_label_list}")

    # meta data
    title = f"cpu-{cpu}"
    save_root = os.path.join("./results", exp_name)
    os.makedirs(save_root, exist_ok=True)

    my_plotter = Plotter(figsize=(20,10))

    print(f"x:{x_list}")
    print(f"box_data_list:{y_list.shape}")


    my_plotter.plot_boxs(
        x=x_list,
        box_data_list=y_list,
        box_label_list=box_label_list,
        x_label="Replicas",
        y_label="Cost",
        save_root=save_root,
        filename=f"{title}.png",
        legend_title="node_num"
    )

    pass


def test_data_filter(node_num=1):
    # 加载csv文件
    df = pd.read_csv(f"./results/res.csv")
    res = data_filter(df=df, node_num=1, cpu=None, memory=None, delta_replicas=None)
    print(res)
    pass


def test_plot_different_cpu(node_num=1, cpu_list=[0.1], delta_replicas_list=[i for i in range(21)], csv_path="./results/res.csv", exp_name="test"):
    # 加载csv文件
    df = pd.read_csv(csv_path)
    plot_different_cpu(
        df,
        node_num=node_num,
        cpu_list=cpu_list,
        exp_name=exp_name,
        delta_replicas_list=delta_replicas_list

    )

def test_plot_different_node_num(cpu=0.1, node_num_list=[1,3,7], csv_path="./results/res.csv", exp_name="test"):
    # 加载csv文件
    df = pd.read_csv(csv_path)
    plot_different_node_num(
        df,
        cpu=cpu,
        node_num_list=node_num_list,
        exp_name=exp_name
    )

def test_plot_box_with_different_node_num(cpu=0.1, node_num_list=[1,3,7], delta_replicas_list=[i for i in range(21)], csv_path="./results/res.csv", exp_name="test"):
    # 加载csv文件
    df = pd.read_csv(csv_path)
    plot_box_with_different_node_num(
        df=df,
        cpu=cpu,
        node_num_list=node_num_list,
        delta_replicas_list=delta_replicas_list,
        exp_name=exp_name
    )


if __name__ == "__main__":
    test_plot_different_cpu(
        node_num=1,
        cpu_list=[0.1],
        csv_path="./results/res_1.csv",
        exp_name="1_node_scaling"
    )

    test_plot_box_with_different_node_num(
        cpu=0.1, 
        node_num_list=[1,3,7], 
        delta_replicas_list=[i for i in range(21)], 
        csv_path="./results/res_2.csv", 
        exp_name="box"
    )