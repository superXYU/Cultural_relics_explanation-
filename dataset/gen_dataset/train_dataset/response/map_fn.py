def single_turn_map_fn(example):
    # 初始化 conversation 列表
    conversation = []
    # 遍历 example 中的每个对话回合
    for idx in range(len(example['conversation'])):
        # 获取当前对话回合的数据
        current_conversation = example['conversation'][idx]
        # 构建新的对话格式
        conversation_turn = {
            'system': current_conversation.get('system', ''),  # 如果没有 system 字段，则默认为空字符串
            'input': current_conversation['input'],  # 用户输入
            'output': current_conversation['output']  # 助手输出
        }
        # 将构建的对话回合添加到 conversation 列表中
        conversation.append(conversation_turn)
    return {'conversation': conversation}