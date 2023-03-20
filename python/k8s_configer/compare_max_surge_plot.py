import pandas as pd
from pyplotter.plot import Plotter
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



def plot_box_with_different_node_num(df, cpu, node_num_list, delta_replicas_list=None, exp_name=None, title="box"):
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
            yy = data["scaling_t"].values
            x.append(xx)
            y.append(yy)

        x_list.append(x)
        y_list.append(y)
        box_label_list.append(str(node_num))

    print(f"len(x_list):{len(x_list)}")
    print(f"len(y_list):{len(y_list)}")
    print(f"box_label_list:{box_label_list}")

    # meta data
    save_root = os.path.join("./figures", exp_name)
    os.makedirs(save_root, exist_ok=True)

    my_plotter = Plotter(figsize=(20,10))


    print(f"x:{x_list}")
    print(f"box_data_list:{y_list}")


    my_plotter.plot_boxes(
        x=x_list[0],
        box_data_list=y_list,
        legend_label_list=box_label_list,
        x_label="Replicas",
        y_label="Scaling Time (s)",
        save_root=save_root,
        filename=f"{title}.png",
        legend_title="Node Num"
    )

    pass


def test_data_filter(node_num=1):
    # 加载csv文件
    df = pd.read_csv(f"./results/res.csv")
    res = data_filter(df=df, node_num=1)
    print(res)
    pass


def test_plot_box_with_different_node_num():
    # 加载csv文件
    df = pd.read_csv("./results/maxSurge-100.csv")
    plot_box_with_different_node_num(
        df=df,
        cpu=0.1,
        delta_replicas_list=[1,2,4,8,10,16,20,30,40],
        exp_name="box-busybox",
        node_num_list=[1],
        title="maxSurge-100"
    )


if __name__ == "__main__":
    # test_plot_different_cpu()

    test_plot_box_with_different_node_num()