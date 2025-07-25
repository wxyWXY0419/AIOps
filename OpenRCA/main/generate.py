import pandas as pd
from datetime import datetime, timedelta
import random
import json
import sys
import os
import pytz
import argparse
from main.prompt import system, user

#把当前文档所在的上一级目录设为绝对根路径
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, parent_dir)

# from scripts.utils import get_chat_completion
from rca.api_router import get_chat_completion

random.seed(42)

# def timestamp2timeperiod(timestamp, timezone) -> str:
#     time = datetime.fromtimestamp(timestamp, timezone)
#     minute = time.minute
#     start_time = time.replace(minute=minute - (minute % 30), second=0, microsecond=0)
#     end_time = start_time + timedelta(minutes=30)
#     start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
#     end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
#     return f"{start_time_str} to {end_time_str}"

# def timestamp2datetime(timestamp, timezone) -> str:
#     time = datetime.fromtimestamp(timestamp, timezone)
#     utc_plus_8_time = time.strftime('%Y-%m-%d %H:%M:%S')
#     return utc_plus_8_time

# def get_one_hour_conflict_failure_flag(meta_data) -> str:
#     sorted_time = sorted(meta_data['timestamp'])
#     half_hour_conflict_failure_flag = {}
#     previous_failure_timestamp = 0
#     for i in range(len(sorted_time)): 
#         timestamp = sorted_time[i]   
#         current_failure_timestamp_left = timestamp // 3600
#         if current_failure_timestamp_left > previous_failure_timestamp:
#             previous_failure_timestamp = current_failure_timestamp_left
#             half_hour_conflict_failure_flag[timestamp] = False
#         else:
#             half_hour_conflict_failure_flag[timestamp] = True
#             half_hour_conflict_failure_flag[sorted_time[i - 1]] = True 
#     return half_hour_conflict_failure_flag

# def get_multi_response_dict(row, meta_data):
#     num = 0
#     multi_dict = {
#         "datetime": [],
#         "component": [],
#         "reason": [],
#     }
#     cand_df = meta_data[meta_data['timestamp']//3600 == row['timestamp']//3600]
#     for idx, cand in cand_df.iterrows():
#         num += 1
#         for key in multi_dict:
#             multi_dict[key].append(cand[key])

#     return num, multi_dict

def query_generate(gt_path, spec_path, extra_spec, query_path, timezone):

    # meta_data = pd.read_csv(gt_path)
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"Ground truth文件不存在: {gt_path}")
    if not os.path.exists(spec_path):
        raise FileNotFoundError(f"specification文件不存在: {spec_path}")
    
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    meta_data = pd.DataFrame(data)
    # 转成DataFrame，列名为uuid和description
    # df = pd.DataFrame([{
    #     "uuid": item["uuid"],
    #     "description": item["Anomaly Description"]
    # }for item in data]) 

    with open(spec_path, "r", encoding="utf8") as f:
        task_templates = json.load(f)

    # one_hour_conflict_failure_flag = get_one_hour_conflict_failure_flag(meta_data)

    # full_task_ID_list = list(task_templates.keys())
    # df = pd.DataFrame(columns=["uuid", "reason", "component", "reasoning_trace"])
    results = [] #用列表存储所有结果

    for idx, row in meta_data.iterrows():
        print(f"processing: {idx}")

        uuid = row['uuid']
        description = row['Anomaly Description']
        # datetime = timestamp2datetime(timestamp, timezone)
        # time_period = timestamp2timeperiod(timestamp, timezone)
        # task_index = random.choice(full_task_ID_list)

        #构造输入输出规范
        # input_specification = "```known\n"
        # for spec in task_templates['input']:
        #     input_specification += f"- "
        #     input_specification += spec.format(
        #         anomaly_description=description,
        #         uuid=uuid
        #     )
        #     input_specification += "\n"
        # if extra_spec:
        #     input_specification += f"- {extra_spec}\n"
        # input_specification = input_specification.strip() + "\n```"

        # output_specification = "```query\n"
        # for spec in task_templates['output']:
        #     output_specification += f"- "
        #     output_specification += spec.format(
        #         uuid=uuid,
        #         reason="**UNKNOWN**",
        #         component="**UNKNOWN**",
        #         reasoning_trace="**UNKNOWN**",
        #     )
        #     output_specification += "\n"
        # output_specification = output_specification.strip() + "\n```"

        prompt = [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': f"Anomaly Description: {description}\nuuid: {uuid}"},
            ]
        
        # print(scoring_points)
        
        for i in range(3):
            # try:
                instruction = get_chat_completion(
                    messages=prompt,
                    temperature=1.0
                )
                #似乎是冗余语句
                # instruction = instruction
                parsed_instruction = json.loads(instruction)
                break
            # except Exception as e:
            #     print(e)
            #     continue
        
        # new_df = pd.DataFrame([{
        #     "uuid": parsed_instruction['uuid'],
        #     "reason": parsed_instruction['reason'],
        #     "component": parsed_instruction['component'],
        #     "reasoning_trace": parsed_instruction['reasoning_trace']
        # }])
        # df = pd.concat([df, new_df], 
        #                ignore_index=True)
        
        # df.to_csv(query_path, index=False)

        result = {
                    "uuid": parsed_instruction['uuid'],
                    "reason": parsed_instruction['reason'],
                    "component": parsed_instruction['component'],
                    "reasoning_trace": parsed_instruction['reasoning_trace']
        }

        results.append(result)

        with open(query_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"generated: {uuid}")

template = """: {{
        "uuid": {uuid},
        "reason": {reason},
        "component":{component},
        "reasoning_trace":{reasoning_trace},        
    }},\n"""

#定义一个key_field列表，方便进行字段名统一管理
# key_field = ["root cause occurrence datetime", "root cause component", "root cause reason"]
key_field = ["uuid", "reason", "component", "reasoning_trace"]


if __name__ == '__main__':
    """
    Generate the query based on the task specification and save it to the corresponding file
        args:
            d: bool, whether to use default setting or not
            s: str, the path of the task specification config
            r: list, a list of record files to generate query
            q: list, a list of query files to save
            e: list, a list of extra spec you want to add in your query (in addition to the spec in json config). If you don't want to add extra spec, just leave it None.
            t: str, timezone of the location where telemetry is collected
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", type=bool, default=False, help="default setting or not")
    parser.add_argument("-s", type=str, help="the path of the task specification config")
    parser.add_argument("-r", type=str, nargs='+', help="a list of input files to generate query")
    parser.add_argument("-q", type=str, nargs='+', help="a list of query files to save")
    parser.add_argument("-e", type=str, nargs='+', help="a list of extra spec you want to add in your query")
    parser.add_argument("-t", type=str, help="timezone of the location where telemetry is collected")
    args = parser.parse_args()

    if args.d:
        spec_path = 'main/task_specification1.json'
        record_path_list = [
            'dataset/Market/cloudbed-1/record.csv',
            'dataset/Market/cloudbed-2/record.csv',
            'dataset/Bank/record.csv',
            'dataset/Telecom/record.csv',
            'dataset/phaseone/input.json',
        ]
        extra_spec_list = [
            "system: cloudbed-1",
            "system: cloudbed-2",
            None,
            None,
            None,
        ]
        query_path_list = [
            'dataset/Market/cloudbed-1/query.csv',
            'dataset/Market/cloudbed-2/query.csv',
            'dataset/Bank/query.csv',
            'dataset/Telecom/query.csv',
            'dataset/phaseone/query.json',
        ]
        timezone = pytz.timezone('Asia/Shanghai')

    else:
        spec_path = args.s
        record_path_list = args.r
        extra_spec_list = args.e if args.e else [None] * len(args.r)
        query_path_list = args.q
        timezone = pytz.timezone(args.t)

    data_list = list(zip(record_path_list, extra_spec_list, query_path_list))

    for record_path, extra_spec, query_path in data_list:
        print("processing: ", record_path)
        query_generate(record_path, spec_path, extra_spec, query_path, timezone)