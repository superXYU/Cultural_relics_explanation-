#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024.4.16
# @Author  : HinGwenWong

import copy
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from utils.web_configs import WEB_CONFIGS

# 初始化 Streamlit 页面配置
st.set_page_config(
    page_title="文物小助手",
    page_icon="root/copy/pages/logo.jpg",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.rag.rag_worker import gen_rag_db
from utils.tools import resize_image

from utils.model_loader import RAG_RETRIEVER  # isort:skip


@st.experimental_dialog("文物详情", width="large")
def instruction_dialog(instruction_path):
    """
    显示产品说明书的popup窗口。

    通过给定的说明书路径，将文件内容以markdown格式在Streamlit应用中显示出来，并提供一个“确定”按钮供用户确认阅读。

    Args:
        instruction_path (str): 说明书的文件路径，该文件应为文本文件，并使用utf-8编码。
    """
    print(f"Show instruction : {instruction_path}")
    with open(instruction_path, "r", encoding="utf-8") as f:
        instruct_lines = "".join(f.readlines())

    st.warning("一定要点击下方的【确定】按钮离开该页面", icon="⚠️")
    st.markdown(instruct_lines)
    st.warning("一定要点击下方的【确定】按钮离开该页面", icon="⚠️")
    if st.button("确定"):
        st.rerun()


def on_btton_click(*args, **kwargs):
    """
    按钮点击事件的回调函数。
    """

    # 根据按钮类型执行相应操作
    if kwargs["type"] == "check_instruction":
        # 显示文物详情页
        st.session_state.show_instruction_path = kwargs["instruction_path"]

    elif kwargs["type"] == "process_sales":
        # 切换到文物页面
        st.session_state.page_switch = "pages/cultural_relics_explanation.py"

        # 更新会话状态中的产品信息
        st.session_state.hightlight = kwargs["heighlights"]
        product_info_struct = copy.deepcopy(st.session_state.product_info_struct_template)
        product_info_str = product_info_struct[0].replace("{name}", kwargs["product_name"])
        product_info_str += product_info_struct[1].replace("{highlights}", st.session_state.hightlight)

        # 生成文物文案 prompt
        st.session_state.first_input = copy.deepcopy(st.session_state.first_input_template).replace(
            "{product_info}", product_info_str
        )

        # 更新图片路径和产品名称
        st.session_state.image_path = kwargs["image_path"]
        st.session_state.product_name = kwargs["product_name"]


        # 设置为默认数字人视频路径
        st.session_state.digital_human_video_path = WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_PATH

        # # 清空语音
        # if ENABLE_TTS:
        #     for message in st.session_state.messages:
        #         if "wav" not in message:
        #             continue
        #         Path(message["wav"]).unlink()

        # 清空历史对话
        st.session_state.messages = []


def make_product_container(product_name, product_info, image_height, each_card_offset):
    """
    创建并展示产品信息容器。

    参数:
    - product_name: 产品名称。
    - product_info: 包含产品信息的字典，需包括图片路径、特点和说明书路径。
    - image_height: 图片展示区域的高度。
    - each_card_offset: 容器内各部分间距。
    """

    # 创建带边框的产品信息容器，设置高度
    with st.container(border=True, height=image_height + each_card_offset):

        # 页面标题
        st.header(product_name)

        # 划分左右两列，左侧为图片，右侧为商品信息
        image_col, info_col = st.columns([0.2, 0.8])

        # 图片展示区域
        with image_col:
            # print(f"Loading {product_info['images']} ...")
            image = resize_image(product_info["images"], max_height=image_height)
            st.image(image, channels="bgr")

        # 产品信息展示区域
        with info_col:

            # 特点展示
            st.subheader("特点", divider="grey")

            heighlights_str = "、".join(product_info["heighlights"])
            st.text(heighlights_str)

            # 说明书按钮
            st.subheader("文物详情", divider="grey")
            st.button(
                "查看",
                key=f"check_instruction_{product_name}",
                on_click=on_btton_click,
                kwargs={
                    "type": "check_instruction",
                    "product_name": product_name,
                    "instruction_path": product_info["instruction"],
                },
            )
            # st.button("更新", key=f"update_manual_{product_name}")

            # 讲解按钮
            st.subheader("讲解员", divider="grey")
            st.button(
                "开始讲解",
                key=f"process_sales_{product_name}",
                on_click=on_btton_click,
                kwargs={
                    "type": "process_sales",
                    "product_name": product_name,
                    "heighlights": heighlights_str,
                    "image_path": product_info["images"],
                },
            )


def delete_old_files(directory, limit_time_s=60 * 60 * 5):
    """
    删除指定目录下超过一定时间的文件。

    :param directory: 要检查和删除文件的目录路径
    """
    # 获取当前时间戳
    current_time = time.time()

    # 遍历目录下的所有文件和子目录
    for file_path in Path(directory).iterdir():

        # 获取文件的修改时间戳
        file_mtime = os.path.getmtime(file_path)

        # 计算文件的年龄（以秒为单位）
        file_age_seconds = current_time - file_mtime

        # 检查文件是否超过 n 秒
        if file_age_seconds > limit_time_s:
            try:

                if file_path.is_dir():
                    shutil.rmtree(file_path)
                    continue

                # 删除文件
                file_path.unlink()
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")


def get_sales_info():
    """
    从配置文件中加载销售相关信息，并存储到session状态中。

    该函数不接受参数，也不直接返回任何值，但会更新全局的session状态，包括：
    - sales_info: 系统问候语，针对销售角色定制
    - first_input_template: 对话开始时的第一个输入模板
    - product_info_struct_template: 产品信息结构模板

    """

    # 加载对话配置文件
    with open(WEB_CONFIGS.CONVERSATION_CFG_YAML_PATH, "r", encoding="utf-8") as f:
        dataset_yaml = yaml.safe_load(f)

    # 从配置中提取角色信息
    sales_info = dataset_yaml["role_type"][WEB_CONFIGS.SALES_NAME]

    # 从配置中提取对话设置相关的信息
    system = dataset_yaml["conversation_setting"]["system"]
    first_input = dataset_yaml["conversation_setting"]["first_input"]
    product_info_struct = dataset_yaml["product_info_struct"]

    # 将销售角色名和角色信息插入到 system prompt
    system_str = system.replace("{role_type}", WEB_CONFIGS.SALES_NAME).replace("{character}", "、".join(sales_info))

    # 更新session状态，存储销售相关信息
    st.session_state.sales_info = system_str
    st.session_state.first_input_template = first_input
    st.session_state.product_info_struct_template = product_info_struct


def init_product_info():
    # 读取 yaml 文件
    with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
        product_info_dict = yaml.safe_load(f)

    # 根据 ID 排序，避免乱序
    product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["id"]))

    product_name_list = list(product_info_dict.keys())

    # 生成文物信息
    for row_id in range(0, len(product_name_list), WEB_CONFIGS.EACH_ROW_COL):
        for col_id, col_handler in enumerate(st.columns(WEB_CONFIGS.EACH_ROW_COL)):
            with col_handler:
                if row_id + col_id >= len(product_name_list):
                    continue

                product_name = product_name_list[row_id + col_id]
                make_product_container(
                    product_name, product_info_dict[product_name], WEB_CONFIGS.PRODUCT_IMAGE_HEIGHT, WEB_CONFIGS.EACH_CARD_OFFSET
                )

    return len(product_name_list)


def init_tts():
    # TTS 初始化
    if "gen_tts_checkbox" not in st.session_state:
        st.session_state.gen_tts_checkbox = WEB_CONFIGS.ENABLE_TTS
    if WEB_CONFIGS.ENABLE_TTS:
        # 清除 1 小时之前的所有语音
        Path(WEB_CONFIGS.TTS_WAV_GEN_PATH).mkdir(parents=True, exist_ok=True)
        delete_old_files(WEB_CONFIGS.TTS_WAV_GEN_PATH)


def init_digital_human():
    # 数字人 初始化
    if "digital_human_video_path" not in st.session_state:
        st.session_state.digital_human_video_path = WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_PATH
    if "gen_digital_human_checkbox" not in st.session_state:
        st.session_state.gen_digital_human_checkbox = WEB_CONFIGS.ENABLE_DIGITAL_HUMAN

    if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
        # 清除 1 小时之前的所有视频
        Path(WEB_CONFIGS.DIGITAL_HUMAN_GEN_PATH).mkdir(parents=True, exist_ok=True)
        # delete_old_files(st.session_state.digital_human_root)


def init_asr():
    # 清理 ASR 旧文件
    if WEB_CONFIGS.ENABLE_ASR and Path(WEB_CONFIGS.ASR_WAV_SAVE_PATH).exists():
        delete_old_files(WEB_CONFIGS.ASR_WAV_SAVE_PATH)

    st.session_state.asr_text_cache = ""


def main():
    """
    初始化页面配置，加载模型，处理页面跳转，并展示商品信息。
    """
    print("Starting...")

    # 初始化页面跳转
    if "page_switch" not in st.session_state:
        st.session_state.page_switch = "app.py"
    st.session_state.current_page = "app.py"

    # 显示商品说明书
    if "show_instruction_path" not in st.session_state:
        st.session_state.show_instruction_path = "X-X"
    if st.session_state.show_instruction_path != "X-X":
        instruction_dialog(st.session_state.show_instruction_path)
        st.session_state.show_instruction_path = "X-X"

    # 判断是否需要跳转页面
    if st.session_state.page_switch != st.session_state.current_page:
        st.switch_page(st.session_state.page_switch)

    # TTS 初始化
    init_tts()

    # 数字人 初始化
    init_digital_human()

    # ASR 初始化
    init_asr()

    if "enable_agent_checkbox" not in st.session_state:
        st.session_state.enable_agent_checkbox = WEB_CONFIGS.ENABLE_AGENT

        if WEB_CONFIGS.AGENT_DELIVERY_TIME_API_KEY is None or WEB_CONFIGS.AGENT_WEATHER_API_KEY is None:
            WEB_CONFIGS.ENABLE_AGENT = False
            st.session_state.enable_agent_checkbox = False

    # 获取销售信息
    if "sales_info" not in st.session_state:
        get_sales_info()

    # 添加页面导航页
    # st.sidebar.page_link("app.py", label="商品页", disabled=True)
    # st.sidebar.page_link("./pages/selling_page.py", label="主播卖货")

    # 主页标题
    st.title("Explanation 文物 —— 讲解助手")
    st.header("文物页")

    # 说明
    st.info(
        "这是助手后台，这里需要讲解员讲解的文物目录，选择一个文物，点击【开始讲解】即可跳转到讲解员讲解页面。如果需要加入更多文物，点击下方的添加按钮即可",
        icon="ℹ️",
    )

    # 初始文物列表
    product_num = init_product_info()

    # 侧边栏显示文物数量
    with st.sidebar:
        # 标题
        st.header("Explanation 文物 —— 讲解助手", divider="grey")
        st.subheader(f"讲解员后台信息", divider="grey")
        st.markdown(f"共有文物：{product_num} 件")

        if WEB_CONFIGS.ENABLE_TTS:
            # 是否生成 TTS
            st.subheader(f"TTS 配置", divider="grey")
            st.session_state.gen_tts_checkbox = st.toggle("生成语音", value=st.session_state.gen_tts_checkbox)

        if WEB_CONFIGS.ENABLE_DIGITAL_HUMAN:
            # 是否生成 数字人
            st.subheader(f"数字人 配置", divider="grey")
            st.session_state.gen_digital_human_checkbox = st.toggle(
                "生成数字人视频", value=st.session_state.gen_digital_human_checkbox
            )


    # 添加新文物上传表单
    with st.form(key="add_product_form"):
        product_name_input = st.text_input(label="添加文物名称")
        heightlight_input = st.text_input(label="添加文物特性，以'、'隔开")
        product_image = st.file_uploader(label="上传商品图片", type=["png", "jpg", "jpeg", "bmp"])
        product_instruction = st.file_uploader(label="上传文物详情", type=["md"])
        submit_button = st.form_submit_button(label="提交", disabled=WEB_CONFIGS.DISABLE_UPLOAD)

        if WEB_CONFIGS.DISABLE_UPLOAD:
            st.info(
                "Github 上面的代码已支持上传新商品逻辑。\n但因开放性的 Web APP 没有新增商品审核机制，暂不在此开放上传商品。\n您可以 clone 本项目到您的机器启动即可使能上传按钮",
                icon="ℹ️",
            )

        if submit_button:
            update_product_info(
                product_name_input,
                heightlight_input,
                product_image,
                product_instruction,
            )


def update_product_info(
    product_name_input, heightlight_input, product_image, product_instruction
):
    """
    更新产品信息的函数。

    参数:
    - product_name_input: 商品名称输入，字符串类型。
    - heightlight_input: 商品特性输入，字符串类型。
    - product_image: 商品图片，图像类型。
    - product_instruction: 商品说明书，文本类型。

    返回值:
    无。该函数直接操作UI状态，不返回任何值。
    """

    # TODO 可以不输入图片和特性，大模型自动生成一版让用户自行选择

    # 检查入参
    if product_name_input == "" or heightlight_input == "":
        st.error("文物名称和特点不能为空")
        return

    if product_image is None or product_instruction is None:
        st.error("图片和详情页不能为空")
        return

    # 显示上传状态，并执行上传操作
    with st.status("正在上传文物...", expanded=True) as status:

        save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        image_save_path = Path(WEB_CONFIGS.PRODUCT_IMAGES_DIR).joinpath(f"{save_tag}{Path(product_image.name).suffix}")
        instruct_save_path = Path(WEB_CONFIGS.PRODUCT_INSTRUCTION_DIR).joinpath(
            f"{save_tag}{Path(product_instruction.name).suffix}"
        )

        st.write("图片保存中...")
        with open(image_save_path, "wb") as file:
            file.write(product_image.getvalue())

        st.write("详情页保存中...")
        with open(instruct_save_path, "wb") as file:
            file.write(product_instruction.getvalue())

        st.write("更新文物详情页...")
        with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "r", encoding="utf-8") as f:
            product_info_dict = yaml.safe_load(f)

        # 排序防止乱序
        product_info_dict = dict(sorted(product_info_dict.items(), key=lambda item: item[1]["id"]))
        max_id_key = max(product_info_dict, key=lambda x: product_info_dict[x]["id"])

        product_info_dict.update(
            {
                product_name_input: {
                    "heighlights": heightlight_input.split("、"),
                    "images": str(image_save_path),
                    "instruction": str(instruct_save_path),
                    "id": product_info_dict[max_id_key]["id"] + 1,
                }
            }
        )

        # 备份
        if Path(WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH).exists():
            Path(WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH).unlink()
        shutil.copy(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, WEB_CONFIGS.PRODUCT_INFO_YAML_BACKUP_PATH)

        # 覆盖保存
        with open(WEB_CONFIGS.PRODUCT_INFO_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(product_info_dict, f, allow_unicode=True)

        st.write("生成数据库...")
        if WEB_CONFIGS.ENABLE_RAG:
            # 重新生成 RAG 向量数据库
            gen_rag_db(force_gen=True)

            # 重新加载 retriever
            RAG_RETRIEVER.pop("default")
            RAG_RETRIEVER.get(fs_id="default", config_path=WEB_CONFIGS.RAG_CONFIG_PATH, work_dir=WEB_CONFIGS.RAG_VECTOR_DB_DIR)

        # 更新状态
        status.update(label="添加文物成功!", state="complete", expanded=False)

        st.toast("添加文物成功!", icon="🎉")

        with st.spinner("准备刷新页面..."):
            time.sleep(3)

        # 刷新页面
        st.rerun()


if __name__ == "__main__":
    # streamlit run app.py --server.address=0.0.0.0 --server.port 7860

    # print("Starting...")
    main()