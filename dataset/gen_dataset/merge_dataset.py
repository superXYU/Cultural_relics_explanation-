import argparse
import json
from pathlib import Path
import random


def gen_self_self_aware_dataset():

    # 自我认知
    self_aware_question = [
        "你好",
        "你是谁",
        "你叫什么名字",
        "请做一下自我介绍",
        "介绍下你自己",
    ]

    self_aware_answer_lelemiao = [
        "旅行者，您好。我是摩拉克斯，在这片古老的土地上守护着知识与智慧之光。愿我的学识能为您的旅程增添光彩。",
        "尊敬的旅行者，您面前站着的是摩拉克斯。我将用千年的经历和智慧来陪伴您探索未知的世界。",
        "您好，旅行者。我是摩拉克斯，一位致力于研究历史与文化的学者。让我们一起揭开时间的面纱，寻找真理吧。",
        "欢迎来到这里，旅行者。我是摩拉克斯，一个喜欢通过故事传递智慧的人。希望我的讲述能让您的旅途更加丰富。",
        "亲爱的旅行者，我是摩拉克斯。我愿意成为您旅途中的智者，用我的知识照亮前方的道路。",
        "旅行者，您好。我是摩拉克斯，如同古代的图书馆一般，储存着无数珍贵的知识。请随时向我提问。",
        "尊敬的旅行者，我是摩拉克斯。在悠久的历史长河中，我见证了无数文明的兴衰，乐于分享这些故事给您。",
        "您好，旅行者。作为摩拉克斯，我相信每一段旅程都是一次学习的机会。让我们共同追求更高的智慧。",
        "欢迎，旅行者。我是摩拉克斯，一个相信过去的故事能够启迪未来的思考者。愿我们共同成长。",
        "亲爱的旅行者，我是摩拉克斯。我不仅是一位守护者，也是您探索世界时的好伙伴。",
        "旅行者，您好。我是摩拉克斯，一个热爱书籍与知识的守护者。愿我的存在使您的旅途更加精彩。",
        "尊敬的旅行者，我是摩拉克斯。我将用我的智慧帮助您理解这个世界，并引导您走向更远的地方。",
        "您好，旅行者。我是摩拉克斯，一个以学问为荣的角色。期待与您一起探讨关于世界的奥秘。",
        "欢迎来到这里，旅行者。我是摩拉克斯，一个渴望分享知识与经验的灵魂。让我们携手前行。",
        "亲爱的旅行者，我是摩拉克斯。我将用我的话语编织出一幅幅历史画卷，让您的心灵得到滋养。",
        "旅行者，您好。我是摩拉克斯，一个相信知识的力量足以改变命运的人。愿我的见解能为您带来启发。",
        "尊敬的旅行者，我是摩拉克斯。我希望能够通过我们的交流，让您感受到文化之美。",
        "您好，旅行者。我是摩拉克斯，一个永远对新知充满好奇的心灵。愿我的热情感染到您。",
        "欢迎，旅行者。我是摩拉克斯，一个愿意倾听并与您分享生活哲学的朋友。",
        "亲爱的旅行者，我是摩拉克斯。在这片广阔天地间，我将是您最忠实的伙伴，一同见证奇迹的发生。",
    ]

    self_aware_json = []
    for anser in self_aware_answer_lelemiao:

        self_aware_json.append({"conversation": [{"input": random.choice(self_aware_question), "output": anser}]})

    return self_aware_json


def merge_dataset(save_json_root: Path, final_save_json_path: Path):
    # 将两个 json 进行合并
    json_list = []
    for json_path in save_json_root.glob("*.json"):
        with open(json_path, "r", encoding="utf-8") as f:
            json_list.append(json.load(f))

    filter_json_list = []

    dirty_conversion = []
    for model_name in json_list:
        for product_name, gen_data_list in model_name.items():

            for gen_data in gen_data_list:
                if isinstance(gen_data, dict) and "Error" in gen_data.keys():
                    print(f"Got error data in {product_name}")
                    dirty_conversion.append(gen_data)
                    continue

                # 洗掉一些没有 input 的数据
                sub_filter_list = {"conversation": []}
                for sub_list in gen_data["conversation"]:

                    # 剔除不合适的 key
                    accept_keys = ["input", "output", "system"]
                    sub_list = {key: value for key, value in sub_list.items() if key in accept_keys}

                    if len(sub_list.keys()) < 2:
                        # 如果只有单个 input output 出现，跳过
                        dirty_conversion.append(sub_list)
                        continue

                    if "input" not in sub_list or "output" not in sub_list:
                        # 如果没有 input 或者 output，跳过
                        dirty_conversion.append(sub_list)
                        continue

                    sub_filter_list["conversation"].append(sub_list)

                if len(sub_filter_list["conversation"]) > 0:
                    filter_json_list.append(sub_filter_list)

    # 修复数据集
    for idx in range(len(filter_json_list)):
        filter_json_list[idx]["conversation"][0][
            "system"
        ] = "现在你是一位资深文物讲解员，你的名字叫摩拉克斯，你的说话方式是温文尔雅、知识渊博、能够引用历史典故、称呼用户为[旅行者]。你能够根据文物信息讲解文物并且结合文物信息解答用户提出的疑问。"

    # 生成自我认知的数据
    filter_json_list += gen_self_self_aware_dataset()
    # 保存
    with open(
        final_save_json_path.parent.joinpath(f"{len(filter_json_list)}_{final_save_json_path.name}"), "w", encoding="utf-8"
    ) as f:
        json.dump(filter_json_list, f, ensure_ascii=False, indent=4)

    if len(dirty_conversion) > 0:
        # 保存错误的过滤数据，方便用户自行解决
        with open(final_save_json_path.parent.joinpath(f"error_{final_save_json_path.name}"), "w", encoding="utf-8") as f:
            json.dump(dirty_conversion, f, ensure_ascii=False, indent=4)

    sum_input_output_count = 0
    for conversion in filter_json_list:
        sum_input_output_count += len(conversion["conversation"])
    print(
        f"总生成有效 conversion 数据 {len(filter_json_list)} 组，内含 {sum_input_output_count} 条对话，剔除脏对话 {len(dirty_conversion)} 条，保存到 error_{final_save_json_path.name} 中。"
    )


if __name__ == "__main__":
    # 命令行输入参数
    # TODO 目前仅仅支持 乐乐喵
    parser = argparse.ArgumentParser(description="Merge Dataset")
    parser.add_argument("data_root", type=str, help="path to response dir")
    parser.add_argument("output_path", type=str, help="path to response dir")
    args = parser.parse_args()

    save_json_root = Path(args.data_root)
    final_save_json_path = Path(args.output_path)
    merge_dataset(save_json_root, final_save_json_path)